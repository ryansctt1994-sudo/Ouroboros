import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.integrate import odeint

# Parameters
R = 2.0
r_minor = R / 2  # Tangential throat condition

# Grid for surface
theta_grid = np.linspace(0, 2*np.pi, 150)
phi_grid = np.linspace(0, 2*np.pi, 150)
theta_g, phi_g = np.meshgrid(theta_grid, phi_grid)

# Torus coordinates
X = R * (1 + 0.5 * np.cos(phi_g)) * np.cos(theta_g)
Y = R * (1 + 0.5 * np.cos(phi_g)) * np.sin(theta_g)
Z = r_minor * np.sin(phi_g)

# Color by ternary state proxy: cos(phi) → +1 (outer) to -1 (near throat)
state_colors = np.cos(phi_g)

# Gaussian curvature approximation for standard torus (analytic formula)
# K = cos(φ) / [r (R + r cos(φ))]
# But scaled here with r_minor = R/2
curvature = np.cos(phi_g) / (r_minor * (R + r_minor * np.cos(phi_g)))

fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

# Surface with state coloring
surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1,
                       facecolors=plt.cm.coolwarm(state_colors),
                       linewidth=0, antialiased=True, shade=True, alpha=0.85)

# Delta-zero throat highlight (φ = π)
theta_throat = np.linspace(0, 2*np.pi, 200)
X_throat = R * (1 - 0.5) * np.cos(theta_throat)  # radius R/2
Y_throat = R * (1 - 0.5) * np.sin(theta_throat)
Z_throat = np.zeros_like(theta_throat)
ax.plot(X_throat, Y_throat, Z_throat, color='black', linewidth=6,
        label='Δ-zero reconciliatory throat')

# ------------------- Geodesics -------------------
# Metric on torus: first fundamental form
# ds² = (R + r cos φ)² dθ² + r² dφ²
def torus_geodesic_eqs(y, t, R, r):
    theta, phi, dtheta, dphi = y
    # Christoffel symbols yield:
    d2theta = -2 * (r / (R + r * np.cos(phi))) * np.sin(phi) * dtheta * dphi
    d2phi = (r * np.sin(phi) / (R + r * np.cos(phi))) * dtheta**2 - np.cos(phi)/r * dphi**2
    return [dtheta, dphi, d2theta, d2phi]

# Initial conditions: several geodesics starting from outer equator, heading inward
num_geos = 8
for i in range(num_geos):
    theta0 = i * 2*np.pi / num_geos
    phi0 = 0.0          # start at +1 outer
    dtheta0 = 0.0       # initial direction mostly radial (toward throat)
    dphi0 = 1.0         # normalized speed
    y0 = [theta0, phi0, dtheta0, dphi0]
    t = np.linspace(0, 15, 1000)  # parameter
    sol = odeint(torus_geodesic_eqs, y0, t, args=(R, r_minor))
    theta_sol, phi_sol = sol[:,0], sol[:,1]
    
    # Convert to Cartesian
    x_geo = R * (1 + 0.5 * np.cos(phi_sol)) * np.cos(theta_sol)
    y_geo = R * (1 + 0.5 * np.cos(phi_sol)) * np.sin(theta_sol)
    z_geo = r_minor * np.sin(phi_sol)
    ax.plot(x_geo, y_geo, z_geo, color='yellow', linewidth=2, alpha=0.8)

# Labels
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('Ouroboros Toroidal Manifold\n'
             'Black: Δ-zero throat | Colored: ternary state (+1 warm → -1 cool)\n'
             'Yellow curves: geodesics inverting smoothly through throat')
ax.legend(loc='upper left')
ax.set_box_aspect([1,1,1])
ax.view_init(elev=25, azim=50)

# Colorbar for state
m = plt.cm.ScalarMappable(cmap=plt.cm.coolwarm)
m.set_array(state_colors)
m.set_clim(-1, 1)
fig.colorbar(m, ax=ax, shrink=0.6, label='Ternary proxy (cos φ): +1 expansion → -1 collapse')

plt.tight_layout()
plt.show()

# Optional: save
# plt.savefig('ouroboros_torus_enhanced_with_geodesics.png', dpi=400, bbox_inches='tight')
