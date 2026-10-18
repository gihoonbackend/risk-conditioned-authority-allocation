import math
import numpy as np

REF_LANE_ID = None
REF_ROAD_ID = None

def vehicle_half_length(vehicle):
    """센터→앞/뒤 범퍼까지 거리 추정 (bounding_box 기반)."""
    try:
        hx = float(vehicle.bounding_box.extent.x)
        return hx if hx > 1e-3 else 2.5  # 기본 승용차 half-length fallback
    except Exception:
        return 2.5


def distance_between(v1, v2):
    loc1 = v1.get_location()
    loc2 = v2.get_location()
    dx, dy = loc1.x - loc2.x, loc1.y - loc2.y
    return math.sqrt(dx * dx + dy * dy)


def get_speed(vehicle):
    v = vehicle.get_velocity()
    return math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)


def distance_along_centerline(ego, lead, cl_pts):
    """센터라인 방향으로 투영한 종방향 거리(사선 영향 줄임)."""
    if cl_pts and len(cl_pts) >= 2:
        p0 = cl_pts[0]
        pN = cl_pts[-1]
        dir_vec = np.array([pN.x - p0.x, pN.y - p0.y])
        norm = np.linalg.norm(dir_vec)
        if norm > 1e-3:
            dir_unit = dir_vec / norm
            rel = np.array([
                lead.get_location().x - ego.get_location().x,
                lead.get_location().y - ego.get_location().y
            ])
            ds = float(np.dot(rel, dir_unit))
            if ds > 0.0:
                return ds
    return distance_between(ego, lead)


def lock_to_ref_lane(base_wp):
    """현재 REF_LANE_ID/REF_ROAD_ID 기준 차선으로 웨이포인트 보정."""
    global REF_LANE_ID, REF_ROAD_ID
    if REF_LANE_ID is None:
        REF_LANE_ID = base_wp.lane_id
        REF_ROAD_ID = base_wp.road_id

    cands = [base_wp]
    w = base_wp
    for _ in range(6):
        w = w.get_left_lane()
        if not w:
            break
        cands.append(w)
    w = base_wp
    for _ in range(6):
        w = w.get_right_lane()
        if not w:
            break
        cands.append(w)
    for c in cands:
        if c.road_id == REF_ROAD_ID and c.lane_id == REF_LANE_ID:
            return c
    for c in cands:
        if c.lane_id == REF_LANE_ID:
            return c
    return base_wp


def get_ref_lane_waypoint(world, location):
    wp = world.get_map().get_waypoint(location, project_to_road=True)
    return lock_to_ref_lane(wp)


def centerline_state(ego, world, ahead_dists=(3.0, 6.0, 9.0, 12.0)):
    """
    여러 전방 웨이포인트로 가상의 센터라인을 만들어 횡방향 상태 계산.
    """
    cur_loc = ego.get_location()
    wp = get_ref_lane_waypoint(world, cur_loc)

    # 센터라인은 현재 차 위치가 아니라 기준 차선의 센터에서 시작
    wp_loc = wp.transform.location
    pts = [wp_loc]
    for d_ahead in ahead_dists:
        nxt = wp.next(d_ahead)
        if nxt:
            pts.append(nxt[0].transform.location)
    if len(pts) < 2:
        # fallback: 단일 웨이포인트 기반
        yaw_wp = math.radians(wp.transform.rotation.yaw)
        yaw_car = math.radians(ego.get_transform().rotation.yaw)
        epsi = (yaw_car - yaw_wp + math.pi) % (2 * math.pi) - math.pi
        # 헤딩이 뒤집혀 있으면 경로 방향을 맞춤 (LQR 선형 영역 유지)
        if abs(epsi) > math.pi / 2:
            yaw_wp = (yaw_wp + math.pi) % (2 * math.pi)
            epsi = (yaw_car - yaw_wp + math.pi) % (2 * math.pi) - math.pi

        forward_wp = np.array([math.cos(yaw_wp), math.sin(yaw_wp)])
        left_wp = np.array([-math.sin(yaw_wp), math.cos(yaw_wp)])
        vec_wp_to_car = np.array([cur_loc.x - wp.transform.location.x, cur_loc.y - wp.transform.location.y])
        ey = float(np.dot(vec_wp_to_car, left_wp))
        v = ego.get_velocity()
        vel = np.array([v.x, v.y])
        eydot = float(np.dot(vel, left_wp))
        epsidot = math.radians(ego.get_angular_velocity().z)
        return ey, eydot, epsi, epsidot, 0.0, pts

    p0 = pts[0]
    pN = pts[-1]
    dir_vec = np.array([pN.x - p0.x, pN.y - p0.y])
    line_len = np.linalg.norm(dir_vec)
    if line_len < 1e-3:
        dir_unit = np.array([math.cos(math.radians(wp.transform.rotation.yaw)),
                             math.sin(math.radians(wp.transform.rotation.yaw))])
    else:
        dir_unit = dir_vec / line_len

    yaw_car = math.radians(ego.get_transform().rotation.yaw)
    yaw_path = math.atan2(dir_unit[1], dir_unit[0])
    epsi = (yaw_car - yaw_path + math.pi) % (2 * math.pi) - math.pi
    flip_dir = False
    if abs(epsi) > math.pi / 2:
        dir_unit = -dir_unit
        flip_dir = True
        yaw_path = math.atan2(dir_unit[1], dir_unit[0])
        epsi = (yaw_car - yaw_path + math.pi) % (2 * math.pi) - math.pi

    # 경로 왼쪽(좌측) 벡터 기준 횡오차(양수면 경로 왼쪽)
    left_vec_path = np.array([-dir_unit[1], dir_unit[0]])
    ego_vec = np.array([cur_loc.x - p0.x, cur_loc.y - p0.y])
    ey = float(np.dot(ego_vec, left_vec_path))

    # 횡속도, 요레이트
    v = ego.get_velocity()
    vel = np.array([v.x, v.y])
    left_vec = np.array([-dir_unit[1], dir_unit[0]])
    eydot = float(np.dot(vel, left_vec))
    epsidot = math.radians(ego.get_angular_velocity().z)

    # 곡률 근사: 3점 원호 기반 (더 타이트한 곡률 반영)
    kappa = 0.0
    if len(pts) >= 3:
        p1 = pts[1]
        p2 = pts[2]
        a = math.hypot(p1.x - p0.x, p1.y - p0.y)
        b = math.hypot(p2.x - p1.x, p2.y - p1.y)
        c = math.hypot(p2.x - p0.x, p2.y - p0.y)
        if a > 1e-3 and b > 1e-3 and c > 1e-3:
            cross = (p1.x - p0.x) * (p2.y - p0.y) - (p1.y - p0.y) * (p2.x - p0.x)
            kappa = 2.0 * cross / (a * b * c)
            if flip_dir:
                kappa = -kappa

    return ey, eydot, epsi, epsidot, kappa, pts
