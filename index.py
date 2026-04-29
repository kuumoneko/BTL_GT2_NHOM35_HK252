import numpy as np
from sympy import symbols, diff, lambdify, sympify, sqrt, exp
import plotly.graph_objects as go

def main_thermal_physics_simulation():
    x_sym, y_sym, z_sym_var = symbols('x y z')

    print("=== CHƯƠNG TRÌNH MÔ PHỎNG TẢN NHIỆT VẬT LÝ (FOURIER LAW) ===")
    
    # 1. THÔNG SỐ VẬT LIỆU & NHIỆT ĐỘ
    materials = {
        "1": {"name": "Nhôm (Aluminium)", "k": 235},
        "2": {"name": "Đồng (Copper)", "k": 400},
        "3": {"name": "Thép (Steel)", "k": 50}
    }
    print("\n[BƯỚC 1] THÔNG SỐ VẬT LIỆU")
    for key, val in materials.items():
        print(f" {key}. {val['name']} (k = {val['k']} W/m·K)")
    
    choice = input("Lựa chọn (1/2/3): ")
    k_val = materials.get(choice, materials["1"])["k"]
    mat_name = materials.get(choice, materials["1"])["name"]

    T_base = float(input("Nhập nhiệt độ nguồn tại đáy (độ C): "))
    alpha = 0.5 

    # 2. NHẬP HÌNH DẠNG
    print("\n[BƯỚC 2] THIẾT LẬP HÌNH HỌC")
    z_str = input("Nhập hàm mặt trên z = f(x,y): ")
    R_limit = float(input("Nhập bán kính đáy R (m): "))

    try:
        f_surface_sym = sympify(z_str)
    except Exception as e:
        print(f"[LỖI] Hàm số không hợp lệ: {e}")
        return

    # 3. PHÂN TÍCH VẬT LÝ FOURIER
    print("\n[BƯỚC 3] PHÂN TÍCH VẬT LÝ (ĐỊNH LUẬT FOURIER)")
    T_expr = T_base * exp(-alpha * z_sym_var)
    dT_dz = diff(T_expr, z_sym_var)
    F_z_sym = -k_val * dT_dz

    print(f" - Hàm nhiệt độ T(z): {T_expr}")
    print(f" - Gradient nhiệt độ dT/dz: {dT_dz}")
    print(f" - Dòng nhiệt thoát lên F_z = -k * dT/dz: {F_z_sym}")

    # 4. TÍNH TOÁN GIẢI TÍCH
    print("\n[BƯỚC 4] GIẢI TÍCH VI PHÂN MẶT")
    dz_dx = diff(f_surface_sym, x_sym)
    dz_dy = diff(f_surface_sym, y_sym)
    ds_factor_sym = sqrt(1 + dz_dx**2 + dz_dy**2)
    
    print(f" - Đạo hàm dz/dx: {dz_dx}")
    print(f" - Đạo hàm dz/dy: {dz_dy}")
    print(f" - Yếu tố diện tích dS: {ds_factor_sym} dA")

    f_z = lambdify((x_sym, y_sym), f_surface_sym, 'numpy')
    f_ds = lambdify((x_sym, y_sym), ds_factor_sym, 'numpy')
    f_dzdx = lambdify((x_sym, y_sym), dz_dx, 'numpy')
    f_dzdy = lambdify((x_sym, y_sym), dz_dy, 'numpy')
    f_flux_z = lambdify(z_sym_var, F_z_sym, 'numpy')

    # 5. TẠO LƯỚI
    grid_res = 200
    r_vals = np.linspace(0, R_limit, grid_res)
    theta_vals = np.linspace(0, 2*np.pi, grid_res)
    R_grid, THETA_grid = np.meshgrid(r_vals, theta_vals)
    X, Y = R_grid * np.cos(THETA_grid), R_grid * np.sin(THETA_grid)
    dA = R_grid * (r_vals[1] - r_vals[0]) * (theta_vals[1] - theta_vals[0])

    Z_vals = f_z(X, Y)
    if np.isscalar(Z_vals): Z_vals = np.full_like(X, Z_vals)
    
    # 6. TÍNH TOÁN TÍCH PHÂN
    print("\n[BƯỚC 5] THỰC THI TÍCH PHÂN SỐ HỌC")
    mask_top = Z_vals >= 0
    mask_base = Z_vals < 0

    # Diện tích mặt cong
    ds_vals = f_ds(X, Y)
    if np.isscalar(ds_vals): ds_vals = np.full_like(X, ds_vals)
    surface_area = np.sum(ds_vals[mask_top] * dA[mask_top])
    print(f" -> Đang tính tích phân mặt loại 1 cho diện tích...")

    # Tích phân thông lượng
    F_z_vals = f_flux_z(Z_vals)
    phi_top = np.sum(F_z_vals[mask_top] * dA[mask_top])
    
    F_z_at_0 = float(F_z_sym.subs(z_sym_var, 0))
    phi_base = np.sum(F_z_at_0 * dA[mask_base])
    print(f" -> Đang tính tích phân mặt loại 2 cho thông lượng nhiệt...")

    # 7. BÁO CÁO
    print("\n" + "="*45)
    print(f" KẾT QUẢ MÔ PHỎNG VẬT LÝ ({mat_name})")
    print("="*45)
    print(f" - Diện tích bề mặt tiếp xúc thực tế : {surface_area:.4f} m²")
    print(f" - Nhiệt độ nguồn tại đáy           : {T_base:.1f} °C")
    print(f" - Nhiệt độ thấp nhất tại đỉnh      : {float(T_expr.subs(z_sym_var, np.max(Z_vals))):.2f} °C")
    print(f" - Công suất thoát qua cánh tản     : {phi_top:.2f} W")
    print(f" - Công suất thoát qua đế hở        : {phi_base:.2f} W")
    print(f" => TỔNG CÔNG SUẤT THOÁT NHIỆT (Φ)  : {phi_top + phi_base:.2f} Watts")
    print("="*45)

    # Hiển thị 3D
    # 1. Vẽ mặt trên (Top surface)
    Z_plot = Z_vals.copy()
    Z_plot[mask_base] = np.nan

    top_surface = go.Surface(
        x=X, y=Y, z=Z_plot,
        colorscale='Hot',
        colorbar=dict(title='Nhiệt độ °C', x=0.85),
        name='Bề mặt tản nhiệt',
        showscale=True
    )

    # 2. Vẽ mặt đáy (Base surface) - Dạng khối đặc màu tối
    base_surface = go.Surface(
        x=X, y=Y, z=np.zeros_like(X),
        colorscale=[[0, 'rgb(80,80,80)'], [1, 'rgb(80,80,80)']],
        showscale=False,
        name='Đáy',
        hoverinfo='skip', # Bỏ qua popup khi trỏ chuột vào đáy
        opacity=0.5
    )

    # 3. Vẽ thành bao xung quanh (Side walls)
    x_outer = X[:, -1]
    y_outer = Y[:, -1]
    # Chỉ lấy phần z >= 0 để không bị lẹm xuống dưới đáy
    z_outer = np.maximum(Z_vals[:, -1], 0)

    v_grid = np.linspace(0, 1, 30)
    X_wall = np.outer(x_outer, np.ones_like(v_grid))
    Y_wall = np.outer(y_outer, np.ones_like(v_grid))
    Z_wall = np.outer(z_outer, v_grid)

    wall_surface = go.Surface(
        x=X_wall, y=Y_wall, z=Z_wall,
        colorscale=[[0, 'rgb(180,180,180)'], [1, 'rgb(180,180,180)']],
        showscale=False,
        name='Thành bao',
        hoverinfo='skip',
        opacity=0.5
    )

    # 4. Vẽ vector thông lượng nhiệt (Plotly dùng go.Cone thay vì Quiver)
    skip = 12
    x_vec = X[mask_top][::skip]
    y_vec = Y[mask_top][::skip]
    z_vec = Z_vals[mask_top][::skip]
    
    # Tính toán vector (hướng thẳng đứng lên trên, độ lớn theo F_z_vals)
    u_vec = np.zeros_like(x_vec)
    v_vec = np.zeros_like(x_vec)
    w_raw = F_z_vals[mask_top][::skip]
    
    # Lọc bỏ các giá trị NaN để tránh lỗi khi vẽ Cone
    valid_mask = ~np.isnan(w_raw)
    x_vec, y_vec, z_vec = x_vec[valid_mask], y_vec[valid_mask], z_vec[valid_mask]
    u_vec, v_vec, w_raw = u_vec[valid_mask], v_vec[valid_mask], w_raw[valid_mask]

    heat_flux = go.Cone(
        x=x_vec, y=y_vec, z=z_vec,
        u=u_vec, v=v_vec, w=w_raw,
        colorscale='Blues',
        sizemode="scaled",
        sizeref=0.3,
        showscale=False,
        name='Vector tỏa nhiệt'
    )

    # 5. Đóng gói và thiết lập khung nhìn (Layout)
    fig = go.Figure(data=[top_surface, base_surface, wall_surface, heat_flux])

    fig.update_layout(
        title=f"<b>Mô phỏng tản nhiệt (Định luật Fourier) - {mat_name}</b>",
        scene=dict(
            xaxis_title='Trục X (m)',
            yaxis_title='Trục Y (m)',
            zaxis_title='Trục Z (Độ cao)',
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.6),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        width=1000,
        height=800,
        margin=dict(l=0, r=0, b=0, t=50)
    )

    fig.show()

if __name__ == "__main__":
    main_thermal_physics_simulation()