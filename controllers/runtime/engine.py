import argparse
import copy
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import random
import shutil
import sys
import time
import traceback
import uuid

import numpy as np

from common import (DEFAULT_CONFIG, HERE, ROOT, build_library, ensure_hash_seed, git_provenance,
                    import_carla, json_digest, load_config, sha256, source_hashes, write_json)
from control import (Controller, ResidualPolicy, guard_residual_authority, lead_control, lead_profile,
                     load_geometry, steering_postprocess)
from metrics import analyze_run, plot_run
from risk import PathResolver, RiskModel


def transform_dict(transform):
    return {"x": transform.location.x, "y": transform.location.y, "z": transform.location.z,
            "pitch": transform.rotation.pitch, "yaw": transform.rotation.yaw, "roll": transform.rotation.roll}


def actor_manifest(actor):
    physics = actor.get_physics_control()
    return {"id": actor.id, "blueprint": actor.type_id, "attributes": dict(actor.attributes),
            "transform": transform_dict(actor.get_transform()),
            "bounding_box_extent_m": {key: float(getattr(actor.bounding_box.extent, key)) for key in ("x", "y", "z")},
            "physics": str(physics), "physics_mass_kg": physics.mass,
            "wheels": [str(wheel) for wheel in physics.wheels]}


def package_versions():
    versions = {"python": sys.version, "platform": platform.platform()}
    for name in ("numpy", "pandas", "torch", "matplotlib"):
        versions[name] = importlib.metadata.version(name)
    return versions


def seed_everything(config):
    import torch

    settings = config["experiment"]
    random.seed(settings["python_seed"])
    np.random.seed(settings["numpy_seed"])
    torch.manual_seed(settings["torch_seed"])
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(settings["torch_seed"])
    torch.use_deterministic_algorithms(settings["torch_deterministic_algorithms"])
    torch.set_num_threads(settings["torch_num_threads"])
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def snapshot_inputs(run_dir, config, hashes):
    for relative, expected in hashes.items():
        destination = run_dir / "source_snapshot" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
        if sha256(destination) != expected:
            raise RuntimeError("Source changed during snapshot: " + relative)
    for name, item in config["artifacts"].items():
        destination = run_dir / "inputs" / (name + Path(item["absolute_path"]).suffix)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item["absolute_path"], destination)
        if sha256(destination) != item["sha256"]:
            raise RuntimeError("Artifact changed during snapshot: " + name)


def clear_vehicle_actors(world, timeout_s):
    """Remove leftover vehicles before a dedicated no-traffic experiment run."""
    actors = list(world.get_actors().filter("vehicle.*"))
    removed_ids = []
    for actor in actors:
        try:
            actor.destroy()
            removed_ids.append(actor.id)
        except RuntimeError:
            pass
    if removed_ids:
        world.tick(timeout_s)
    return removed_ids


def spawn_vehicle(world, config, role, carla):
    simulation = config["simulation"]
    spawn_settings = simulation["spawn"]
    blueprint = world.get_blueprint_library().find(simulation["vehicle_blueprint"])
    for key, value in simulation["blueprint_attributes"].items():
        if not blueprint.has_attribute(key):
            raise ValueError("Blueprint lacks configured attribute: " + key)
        blueprint.set_attribute(key, str(value))
    blueprint.set_attribute("role_name", "revision_" + role)
    location = carla.Location(**spawn_settings[role])
    waypoint = world.get_map().get_waypoint(location, project_to_road=True, lane_type=carla.LaneType.Driving)
    transform = waypoint.transform
    transform.location.z += spawn_settings["z_offset_m"]
    attempts = int(spawn_settings.get("retry_attempts", 1))
    retry_ticks = int(spawn_settings.get("retry_ticks", 0))
    timeout_s = float(spawn_settings.get("retry_timeout_s", 2.0))
    initial_speed = float(spawn_settings.get("initial_speed_mps_by_role", {}).get(
        role, spawn_settings["initial_speed_mps"]))
    if initial_speed < 0:
        raise ValueError("Initial speed must be nonnegative for " + role)
    for attempt in range(1, attempts + 1):
        actor = world.try_spawn_actor(blueprint, transform)
        if actor is not None:
            actor.set_simulate_physics(True)
            actor.apply_control(carla.VehicleControl(hand_brake=False, brake=0, throttle=0, gear=1))
            if initial_speed != 0:
                velocity = transform.get_forward_vector() * initial_speed
                actor.set_target_velocity(velocity)
            return actor, attempt
        for _ in range(retry_ticks):
            world.tick(timeout_s)
    raise RuntimeError("Failed to spawn %s after %d attempt(s)" % (role, attempts))


def execute(config, force=False):
    config = copy.deepcopy(config)
    started = datetime.now(timezone.utc)
    name = started.strftime("%Y%m%dT%H%M%S_%fZ") + "_" + config["experiment"]["scenario"] + "_" + uuid.uuid4().hex[:6]
    run_dir = ROOT / config["experiment"]["output_root"] / name
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "initializing", "started_at_utc": started.isoformat(),
                "command": [sys.executable, *sys.argv], "cwd": str(ROOT), "force": force,
                "config": config, "git": git_provenance(), "versions": package_versions(),
                "source_sha256": source_hashes(), "cache": {"enabled": False, "read": False},
                "execution": {"actual_logged_duration_s": None, "completed_simulation_duration_s": None}}
    manifest["run_signature"] = json_digest({"config": config, "sources": manifest["source_sha256"],
                                              "git_commit": manifest["git"]["commit"], "versions": manifest["versions"]})
    write_json(run_dir / "manifest.json", manifest)
    write_json(run_dir / "resolved_config.json", config)
    events = (run_dir / "console.log").open("a", buffering=1)

    def announce(message):
        line = datetime.now(timezone.utc).isoformat() + " " + message
        print(line, flush=True)
        print(line, file=events)

    world = original_settings = controller = None
    actors = []
    stream = None
    wall_start = time.monotonic()
    try:
        snapshot_inputs(run_dir, config, manifest["source_sha256"])
        library, build = build_library(run_dir / "build")
        manifest["build"] = build
        seed_everything(config)
        risk_model = RiskModel(config)
        resolver = PathResolver(config)
        geometry = load_geometry(config)
        policy = ResidualPolicy(config)
        manifest["execution"]["checkpoint_loaded"] = True
        controller = Controller(library, config)
        carla = import_carla()
        simulation = config["simulation"]
        client = carla.Client(simulation["host"], simulation["port"])
        client.set_timeout(simulation["timeout_s"])
        server_version = client.get_server_version()
        client_version = client.get_client_version()
        if not server_version.startswith(simulation["carla_version"]) or not client_version.startswith(simulation["carla_version"]):
            raise RuntimeError("CARLA version differs from canonical config")
        manifest["carla"] = {"server_version": server_version, "client_version": client_version,
                             "version_strings_identical": server_version == client_version}
        announce("Loading fresh " + simulation["town"])
        world = client.load_world(simulation["town"])
        original_settings = world.get_settings()
        settings = world.get_settings()
        for key in ("synchronous_mode", "fixed_delta_seconds", "substepping", "max_substep_delta_time", "max_substeps", "no_rendering_mode"):
            setattr(settings, key, simulation[key])
        world.apply_settings(settings)
        world.set_weather(getattr(carla.WeatherParameters, simulation["weather_preset"]))
        world_map = world.get_map()
        if world_map.name.split("/")[-1] != simulation["town"]:
            raise RuntimeError("Loaded CARLA Town differs from configuration")
        opendrive = world_map.to_opendrive()
        (run_dir / "inputs" / "map.xodr").write_text(opendrive)
        manifest["carla"].update({"map": world_map.name, "opendrive_sha256": hashlib.sha256(opendrive.encode()).hexdigest(),
                                  "world_settings": str(world.get_settings()), "weather": str(world.get_weather()),
                                  "traffic_manager_used": False, "stochastic_seed_api_used": False})
        manifest["effective_run_signature"] = json_digest({"planned": manifest["run_signature"],
                                                           "build": build, "carla": manifest["carla"]})
        spawn_settings = simulation["spawn"]
        pre_spawn_removed_vehicle_ids = []
        if spawn_settings.get("clear_vehicle_actors_before_spawn", False):
            pre_spawn_removed_vehicle_ids = clear_vehicle_actors(
                world, float(spawn_settings.get("retry_timeout_s", 2.0)))
        for _ in range(int(spawn_settings.get("pre_spawn_settle_ticks", 0))):
            world.tick(float(spawn_settings.get("retry_timeout_s", 2.0)))
        lead, lead_spawn_attempts = spawn_vehicle(world, config, "lead", carla)
        actors.append(lead)
        ego, ego_spawn_attempts = spawn_vehicle(world, config, "ego", carla)
        actors.append(ego)
        manifest["actors_at_spawn"] = {"ego": actor_manifest(ego), "lead": actor_manifest(lead)}
        manifest["execution"]["spawn"] = {
            "pre_spawn_removed_vehicle_ids": pre_spawn_removed_vehicle_ids,
            "lead_attempts": lead_spawn_attempts,
            "ego_attempts": ego_spawn_attempts,
        }
        for _step in range(simulation["spawn"]["settle_ticks"]):
            world.tick()
        snapshot = world.get_snapshot()
        start_elapsed = snapshot.timestamp.elapsed_seconds
        start_frame = snapshot.frame
        offset = geometry["vehicle_half_length"](ego) + geometry["vehicle_half_length"](lead)
        sample_time = simulation["fixed_delta_seconds"]
        previous_steer = 0.0
        evaluation_start = simulation["evaluation_start_s"]
        evaluation_end = simulation.get("evaluation_end_s")
        manifest["execution"].update({"center_to_bumper_offset_m": offset, "initial_frame": start_frame,
                                      "simulation_timestamp_origin": start_elapsed, "evaluation_start_s": evaluation_start,
                                      "evaluation_end_s": evaluation_end,
                                      "controller_samples": 0, "first_path1_time_s": None})
        manifest["status"] = "running"
        write_json(run_dir / "manifest.json", manifest)
        stream = (run_dir / "raw.csv").open("w", newline="", buffering=1)
        writer = None
        last_phase = None
        for step in range(simulation["expected_control_samples"]):
            snapshot = world.get_snapshot()
            if snapshot.frame != start_frame + step:
                raise RuntimeError("Unexpected external tick or frame jump")
            time_s = snapshot.timestamp.elapsed_seconds - start_elapsed
            location = ego.get_location()
            lead_location = lead.get_location()
            path, path_source, path_distance = resolver.resolve([location.x, location.y], time_s)
            if resolver.entered_path1 and manifest["execution"]["first_path1_time_s"] is None:
                manifest["execution"]["first_path1_time_s"] = time_s
                announce("First spatial Path1 entry at %.3f simulation seconds" % time_s)
            ey, eydot, epsi, epsidot, kappa, centerline = geometry["centerline_state"](
                ego, world, ahead_dists=config["controller"]["state_geometry"]["ahead_distances_m"])
            speed, lead_speed = geometry["get_speed"](ego), geometry["get_speed"](lead)
            center_distance = geometry["distance_along_centerline"](ego, lead, centerline)
            bumper_distance = max(center_distance - offset, 0.0)
            risks = risk_model.compute(bumper_distance, speed, lead_speed, kappa, path)
            output = controller.step(speed, bumper_distance, lead_speed, config["controller"]["mpc"]["v_ref_mps"],
                                     [ey, eydot, epsi, epsidot])
            residual = policy.step([ey, eydot, epsi, epsidot, speed, kappa])
            alpha_lon, alpha_lat = risks["alpha_lon"], risks["alpha_lat"]
            ax_command = (1 - alpha_lon) * output["ax_ctg"] + alpha_lon * output["ax_mpc"]
            residual_authority = guard_residual_authority(
                output["delta_lqr"], alpha_lat, residual["residual_filtered_rad"], config["controller"]["rl"])
            delta = output["delta_lqr"] + residual_authority["residual_effective_guarded_rad"]
            steering = steering_postprocess(delta, ey, epsi, previous_steer,
                                            config["controller"]["steering_postprocess"], sample_time)
            previous_steer = steering["steer_applied"]
            scale = config["controller"]["acceleration_to_pedal_scale_mps2"]
            throttle, brake = float(np.clip(ax_command / scale, 0, 1)), float(np.clip(-ax_command / scale, 0, 1))
            target_speed, phase = lead_profile(step * sample_time, config, manifest["execution"]["first_path1_time_s"])
            if phase != last_phase:
                announce("Lead phase=%s at %.3f s; target=%.3f m/s" % (phase, time_s, target_speed))
                last_phase = phase
            ego.apply_control(carla.VehicleControl(throttle=throttle, brake=brake, steer=previous_steer))
            lead.apply_control(lead_control(lead, world_map, target_speed, config["controller"]["lead"], carla))
            closing_speed = speed - lead_speed
            acceleration = ego.get_acceleration()
            forward = ego.get_transform().get_forward_vector()
            row = {"frame": snapshot.frame, "step": step, "time_s": time_s,
                   "snapshot_elapsed_seconds": snapshot.timestamp.elapsed_seconds,
                   "wall_elapsed_s": time.monotonic() - wall_start,
                   "evaluation_sample": (step * sample_time >= evaluation_start
                                         and (evaluation_end is None or step * sample_time <= evaluation_end)),
                   "path1_started": resolver.entered_path1, "active_path": path,
                   "path_source": path_source, "path_distance_m": path_distance,
                   "ego_x": location.x, "ego_y": location.y, "ego_z": location.z,
                   "lead_x": lead_location.x, "lead_y": lead_location.y,
                   "vx_mps": speed, "lead_speed_mps": lead_speed, "lead_target_mps": target_speed,
                   "event_phase": phase, "d_center_m": center_distance, "d_bumper_m": bumper_distance,
                   "center_to_bumper_offset_m": offset, "dref_m": output["dref"],
                   "ey_m": ey, "eydot_mps": eydot, "epsi_rad": epsi, "epsidot_radps": epsidot,
                   "kappa_raw": kappa, "ax_command_mps2": ax_command,
                   "ax_measured_body_mps2": acceleration.x * forward.x + acceleration.y * forward.y + acceleration.z * forward.z,
                   "throttle": throttle, "brake": brake, "ttc_valid": closing_speed > 1e-3,
                   "ttc_s": bumper_distance / closing_speed if closing_speed > 1e-3 else None,
                   **output, **residual, **residual_authority, **steering, **risks}
            if not all(math.isfinite(value) for value in row.values() if isinstance(value, (int, float))):
                raise RuntimeError("Nonfinite numeric log value")
            if writer is None:
                writer = csv.DictWriter(stream, fieldnames=list(row))
                writer.writeheader()
            writer.writerow(row)
            next_frame = world.tick()
            if next_frame != snapshot.frame + 1:
                raise RuntimeError("CARLA failed to advance exactly one frame")
            manifest["execution"]["controller_samples"] = step + 1
            manifest["execution"]["completed_simulation_duration_s"] = world.get_snapshot().timestamp.elapsed_seconds - start_elapsed
            if (step + 1) % 200 == 0:
                announce("%s %.1f/%.1f s path=%s alpha=%.3f vx=%.2f gap=%.2f" % (
                    config["experiment"]["scenario"], (step + 1) * sample_time, simulation["duration_s"], path, risks["alpha_shared"], speed, bumper_distance))
                write_json(run_dir / "manifest.json", manifest)
        stream.close()
        stream = None
        execution = manifest["execution"]
        execution["actual_logged_duration_s"] = execution["completed_simulation_duration_s"]
        execution["logged_sample_span_s"] = time_s
        execution["wall_duration_s"] = time.monotonic() - wall_start
        config["simulation"]["actual_logged_duration_s"] = execution["actual_logged_duration_s"]
        write_json(run_dir / "resolved_config.json", config)
        summary = analyze_run(run_dir, config, execution)
        plot_run(run_dir)
        manifest["status"] = "passed" if summary["technical_checks_passed"] else "failed_checks"
        if manifest["status"] == "passed" and summary["warnings"]:
            manifest["status"] = "passed_with_warnings"
        manifest["checks"] = summary["checks"]
        manifest["warnings"] = summary["warnings"]
        announce("Finished: " + manifest["status"])
    except Exception as error:
        manifest["status"] = "failed"
        manifest["execution"]["raised_error"] = True
        manifest["error"] = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
        if "time_s" in locals():
            manifest["failure_context"] = {"simulation_time_s": time_s, "step": step,
                                           "ego_x": location.x, "ego_y": location.y, "ego_z": location.z}
        announce("FAILED: " + str(error))
        print(traceback.format_exc(), file=events)
    finally:
        if stream is not None:
            stream.close()
        execution = manifest["execution"]
        completed = execution.get("completed_simulation_duration_s")
        if completed is not None:
            execution["actual_logged_duration_s"] = completed
            config["simulation"]["actual_logged_duration_s"] = completed
            write_json(run_dir / "resolved_config.json", config)
        if manifest["status"] == "failed" and (run_dir / "raw.csv").exists():
            try:
                analyze_run(run_dir, config, execution)
                plot_run(run_dir)
            except Exception as error:
                manifest["partial_analysis_error"] = str(error)
        if controller is not None:
            controller.close()
        cleanup_errors = []
        for actor in reversed(actors):
            try:
                actor.destroy()
            except RuntimeError as error:
                cleanup_errors.append(str(error))
        if actors and world is not None and original_settings is not None:
            try:
                if world.get_settings().synchronous_mode:
                    world.tick(float(config["simulation"]["spawn"].get("retry_timeout_s", 2.0)))
            except RuntimeError as error:
                cleanup_errors.append(str(error))
        if world is not None and original_settings is not None:
            try:
                world.apply_settings(original_settings)
            except RuntimeError as error:
                cleanup_errors.append(str(error))
        manifest["cleanup_errors"] = cleanup_errors
        manifest["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        events.flush()
        manifest["outputs"] = {str(path.relative_to(run_dir)): sha256(path) for path in run_dir.iterdir()
                               if path.is_file() and path.name != "manifest.json"}
        write_json(run_dir / "manifest.json", manifest)
        events.close()
    return run_dir, manifest

