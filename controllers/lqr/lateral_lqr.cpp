// lateral_lqr.cpp
#include "lateral_lqr.hpp"
#include "agentix_utils.hpp"
#include <array>
#include <cmath>
#include <algorithm>

static Mat4 add(const Mat4&A,const Mat4&B){
    Mat4 C{};
    for(int i=0;i<4;i++) for(int j=0;j<4;j++)
        C.a[i][j]=A.a[i][j]+B.a[i][j];
    return C;
}
static Mat4 subm(const Mat4&A,const Mat4&B){
    Mat4 C{};
    for(int i=0;i<4;i++) for(int j=0;j<4;j++)
        C.a[i][j]=A.a[i][j]-B.a[i][j];
    return C;
}
static Mat4 mul(const Mat4&A,const Mat4&B){
    Mat4 C{};
    for(int i=0;i<4;i++) for(int j=0;j<4;j++){
        double s=0;
        for(int k=0;k<4;k++) s+=A.a[i][k]*B.a[k][j];
        C.a[i][j]=s;
    }
    return C;
}
static Mat4 scale(const Mat4&A,double s){
    Mat4 C=A;
    for(int i=0;i<4;i++) for(int j=0;j<4;j++)
        C.a[i][j]*=s;
    return C;
}
static void set_eye(Mat4& I){
    for(int i=0;i<4;i++) for(int j=0;j<4;j++)
        I.a[i][j]=(i==j);
}

template<int C>
static void solve4(const double M_in[4][4], const double N_in[4][C], double X_out[4][C]){
    double A[4][4+C];
    for(int i=0;i<4;i++){
        for(int j=0;j<4;j++) A[i][j]=M_in[i][j];
        for(int j=0;j<C;j++)   A[i][4+j]=N_in[i][j];
    }
    for(int col=0; col<4; ++col){
        int piv=col;
        for(int r=col+1;r<4;r++)
            if (std::fabs(A[r][col])>std::fabs(A[piv][col])) piv=r;
        std::swap(A[col], A[piv]);
        double p=A[col][col];
        if(std::fabs(p)<1e-12) p=(p>=0?1e-12:-1e-12);
        for(int j=col;j<4+C;j++) A[col][j]/=p;
        for(int r=0;r<4;r++) if(r!=col){
            double f=A[r][col];
            for(int j=col;j<4+C;j++) A[r][j]-=f*A[col][j];
        }
    }
    for(int i=0;i<4;i++) for(int j=0;j<C;j++)
        X_out[i][j]=A[i][4+j];
}

static void solveN(int N, double* M, double* b){
    for(int col=0; col<N; ++col){
        int piv=col;
        for(int r=col+1;r<N;r++)
            if(std::fabs(M[r*N+col])>std::fabs(M[piv*N+col])) piv=r;
        for(int j=0;j<N;j++) std::swap(M[col*N+j], M[piv*N+j]);
        std::swap(b[col], b[piv]);
        double p=M[col*N+col];
        if(std::fabs(p)<1e-14) p=(p>=0?1e-14:-1e-14);
        for(int j=col;j<N;j++) M[col*N+j]/=p;
        b[col]/=p;
        for(int r=0;r<N;r++) if(r!=col){
            double f=M[r*N+col];
            for(int j=col;j<N;j++) M[r*N+j]-=f*M[col*N+j];
            b[r]-=f*b[col];
        }
    }
}

// ---------- PDF lateral model A(Ux), B(Ux) (continuous) ----------
static void lateralAB_pdf(double Ux, const VehicleParams& p, Mat4& A, Vec4& B){
    Ux = std::max(1e-6, Ux);
    double m=p.m, Iz=p.Iz, lf=p.lf, lr=p.lr, Cf=p.Cf, Cr=p.Cr;
    for(int i=0;i<4;i++){ for(int j=0;j<4;j++) A.a[i][j]=0; B.v[i]=0; }

    // Eq.(4)-(5) in PDF (lateral model)
    A.a[0][1] = 1.0;
    A.a[1][1] = -(2*(Cf+Cr))/(m*Ux);
    A.a[1][2] =  (2*(Cf+Cr))/m;
    A.a[1][3] = -(2*(Cf*lf - Cr*lr))/(m*Ux);
    A.a[2][3] = 1.0;
    A.a[3][1] = -(2*(lf*Cf - lr*Cr))/(Iz*Ux);
    A.a[3][2] =  (2*(lf*Cf - lr*Cr))/Iz;
    A.a[3][3] = -(2*(lf*lf*Cf + lr*lr*Cr))/(Iz*Ux);

    B.v[1] = (2*Cf)/m;
    B.v[3] = (2*lf*Cf)/Iz;
}

// ---------- pole placement (initial stabilizing K) ----------
static std::array<double,4> place_poles_ackermann(const Mat4& A, const Vec4& B,
                                             const std::array<double,4>& lam){
    auto AB = [&](const Mat4& M, const Vec4& v){
        Vec4 y{};
        for(int i=0;i<4;i++){
            double s=0;
            for(int j=0;j<4;j++) s+=M.a[i][j]*v.v[j];
            y.v[i]=s;
        }
        return y;
    };
    Vec4 c0=B, c1=AB(A,B), c2=AB(A, c1), c3=AB(A, c2);
    double Cmat[4][4];
    for(int i=0;i<4;i++){
        Cmat[i][0]=c0.v[i];
        Cmat[i][1]=c1.v[i];
        Cmat[i][2]=c2.v[i];
        Cmat[i][3]=c3.v[i];
    }
    double I4[4][4]={{1,0,0,0},{0,1,0,0},{0,0,1,0},{0,0,0,1}}, Cinv[4][4];
    solve4<4>(Cmat, I4, Cinv);

    double l1=lam[0], l2=lam[1], l3=lam[2], l4=lam[3];
    double a3=-(l1+l2+l3+l4);
    double a2=(l1*l2 + l1*l3 + l1*l4 + l2*l3 + l2*l4 + l3*l4);
    double a1=-(l1*l2*l3 + l1*l2*l4 + l1*l3*l4 + l2*l3*l4);
    double a0=(l1*l2*l3*l4);

    auto A2 = mul(A,A);
    auto A3 = mul(A,A2);
    auto A4 = mul(A,A3);
    Mat4 phi = add(add(add(A4, scale(A3,a3)), scale(A2,a2)), scale(A,a1));
    Mat4 I{}; set_eye(I);
    phi = add(phi, scale(I,a0));

    double e4T_Cinv[4]={Cinv[3][0],Cinv[3][1],Cinv[3][2],Cinv[3][3]};
    std::array<double,4> K{};
    for(int j=0;j<4;j++){
        double s=0;
        for(int k=0;k<4;k++) s+=e4T_Cinv[k]*phi.a[k][j];
        K[j]=s;
    }
    return K;
}

// ---------- continuous Lyapunov: Acl^T P + P Acl = -S ----------
static Mat4 lyap_solve(const Mat4& Acl, const Mat4& Sneg){
    double L[16*16]{}; double b[16]{};
    for(int i=0;i<4;i++) for(int j=0;j<4;j++){
        int row = i*4 + j;
        for(int k=0;k<4;k++){
            int col1 = i*4 + k;  L[row*16 + col1] += Acl.a[k][j]; // Acl^T(j,k)
            int col2 = k*4 + j;  L[row*16 + col2] += Acl.a[k][i]; // Acl^T(i,k)
        }
        b[row] = -Sneg.a[i][j];
    }
    solveN(16, L, b);
    Mat4 P{};
    for(int i=0;i<4;i++) for(int j=0;j<4;j++)
        P.a[i][j]=b[i*4+j];
    return P;
}

// ---------- CARE (Newton–Kleinman) ----------
static Mat4 care_solve(const Mat4& A, const Vec4& B, const LqrOpts& opt){
    std::array<double,4> lam = {-2.0, -3.0, -4.0, -5.0};
    std::array<double,4> K = place_poles_ackermann(A, B, lam);

    Mat4 Q{}; for(int i=0;i<4;i++) Q.a[i][i]=opt.Q[i];
    double R = opt.R;

    for(int it=0; it<60; ++it){
        Mat4 BK{};
        for(int i=0;i<4;i++) for(int j=0;j<4;j++)
            BK.a[i][j]=B.v[i]*K[j];
        Mat4 Acl = subm(A, BK);

        Mat4 S{};
        for(int i=0;i<4;i++) S.a[i][i]=opt.Q[i];
        for(int i=0;i<4;i++) for(int j=0;j<4;j++)
            S.a[i][j] += R * K[i]*K[j];

        Mat4 P = lyap_solve(Acl, S);

        std::array<double,4> Knew{};
        for(int j=0;j<4;j++){
            double s=0;
            for(int i=0;i<4;i++) s += B.v[i]*P.a[i][j];
            Knew[j]= s / R;
        }

        double diff=0;
        for(int j=0;j<4;j++){
            double d=Knew[j]-K[j];
            diff += d*d;
        }
        K = Knew;
        if(diff < 1e-10) return P;
    }

    Mat4 BK{};
    for(int i=0;i<4;i++) for(int j=0;j<4;j++)
        BK.a[i][j]=B.v[i]*K[j];
    Mat4 Acl = subm(A, BK);
    Mat4 S{};
    for(int i=0;i<4;i++) S.a[i][i]=opt.Q[i];
    for(int i=0;i<4;i++) for(int j=0;j<4;j++)
        S.a[i][j] += opt.R * K[i]*K[j];
    return lyap_solve(Acl, S);
}

// ---------- LateralLqr implementation ----------
static std::array<double,4> compute_gain_fixed(const VehicleParams& vp,
                                               const LqrOpts& lqr,
                                               double Ux_nom,
                                               Mat4& S_out){
    Mat4 A{}; Vec4 B{};
    lateralAB_pdf(std::max(1.0, Ux_nom), vp, A, B);

    Mat4 P = care_solve(A, B, lqr);

    std::array<double,4> K{};
    for(int j=0;j<4;j++){
        double s=0;
        for(int i=0;i<4;i++) s += B.v[i]*P.a[i][j];
        K[j]= s / lqr.R;
    }
    // 필요 시 스케일 조정 가능; 현재는 계산값 그대로 사용

    // S = Q + K^T R K (for Vdot estimate)
    Mat4 S{}; for(int i=0;i<4;i++) S.a[i][i]=lqr.Q[i];
    for(int i=0;i<4;i++) for(int j=0;j<4;j++)
        S.a[i][j] += lqr.R * K[i]*K[j];
    S_out = S;
    return K;
}

LateralLqr::LateralLqr(const VehicleParams& vp, const LqrOpts& lqr)
: vp_(vp), lqr_(lqr) {
    K_ = compute_gain_fixed(vp_, lqr_, Ux_nom_, S_);
}

LateralLqrResult LateralLqr::step(double /*Ux*/, const Vec4& x_lat) {
    // 고정된 K를 사용 (실시간 CARE 재계산 없음)
    double ufb = -(K_[0]*x_lat.v[0] + K_[1]*x_lat.v[1] +
                   K_[2]*x_lat.v[2] + K_[3]*x_lat.v[3]);
    double delta_cmd = ufb;

    // 1) deadband: very small ey/epsi에서는 0으로 눌러 토글 방지
    if (std::fabs(x_lat.v[0]) <= ey_deadband_ &&
        std::fabs(x_lat.v[2]) <= epsi_deadband_) {
        delta_cmd = 0.0;
    }

    // 2) rate limit to avoid bang-bang switching
    double delta_max_step = delta_rate_max_ * Ts_;
    double delta_min = prev_delta_ - delta_max_step;
    double delta_max = prev_delta_ + delta_max_step;
    delta_cmd = clampv(delta_cmd, delta_min, delta_max);
    prev_delta_ = delta_cmd;

    auto quad = [&](const Vec4& xv){
        double s=0;
        for(int i=0;i<4;i++) for(int j=0;j<4;j++)
            s += xv.v[i]*S_.a[i][j]*xv.v[j];
        return s;
    };
    double Vdot_nom = -quad(x_lat);

    LateralLqrResult res;
    res.delta_cmd = delta_cmd;
    res.K         = K_;
    res.Vdot_nom  = Vdot_nom;
    return res;
}
