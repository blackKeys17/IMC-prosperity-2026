import numpy as np
import matplotlib.pyplot as plt

def research_multiplier(research_invest):
    return 200_000 * np.log(1 + research_invest) / np.log(1 + 100)

def scale_multiplier(scale_invest):
    return 7 * scale_invest / 100

def pnl(research_invest, scale_invest, speed_invest, speed_multiplier):
    total_invest = research_invest + scale_invest + speed_invest
    # Use np.where to handle the condition element-wise for the meshgrid
    result = (research_multiplier(research_invest) * scale_multiplier(scale_invest) * speed_multiplier) - 50000 * total_invest / 100
    return np.where(total_invest <= 100.0, result, np.nan)

speed_invest = 20
speed_multiplier = 0.5
# Research axis
x = np.linspace(0, 100 - speed_invest, 400) # Reduced resolution for faster rendering
# Scale axis
y = np.linspace(0, 100 - speed_invest, 400)

x, y = np.meshgrid(x, y)
z = pnl(x, y, speed_invest, speed_multiplier)

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# create a basic 3d surface plot
surf = ax.plot_surface(x, y, z, cmap='viridis', edgecolor='none')

# add labels and colorbar
ax.set_xlabel('research investment')
ax.set_ylabel('scale investment')
ax.set_zlabel('pnl')
ax.set_title('3d pnl surface')
ax.view_init(elev=30, azim=-135)
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

plt.show()