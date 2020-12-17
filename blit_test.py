import matplotlib.pyplot as plt
import numpy as np
import time
bg_cache = None
current_timer = None


def onclick(event):
    global current_timer
    j = 0
    cv = event.canvas
    fig = cv.figure
    frames = 100

    def update():
        nonlocal j
        # restore the background
        cv.restore_region(bg_cache)

        # update the data

        ii = j * np.pi / frames
        y1 = y * np.sin(ii)

        # update the line on the fixed limit axes
        line1.set_ydata(y1)
        ax.draw_artist(line1)

        # update the line on the limit adjusted axes
        line2.set_ydata(-y1)
        ax2.set_ylim(y1.min(), y1.max())
        fig.draw_artist(ax2)

        # update the screen
        cv.blit(fig.bbox)
        # update counter
        j += 1
        # if we are more than 100 times through, bail!
        if j > frames:
            print(f'fps : {frames / (time.time() - start_time)}')
            return False

    start_time = time.time()
    current_timer = cv.new_timer(
        interval=100, callbacks=[(update, (), {})])

    current_timer.start()


def ondraw(event):
    global bg_cache
    cv = event.canvas
    fig = cv.figure
    bg_cache = cv.copy_from_bbox(fig.bbox)

    ax.draw_artist(line1)
    fig.draw_artist(ax2)


x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)

fig = plt.figure()
ax = fig.add_subplot(1, 2, 1)
line1, = ax.plot(x, y, animated=True)

ax2 = fig.add_subplot(1, 2, 2)
ax2.set_animated(True)
line2, = ax2.plot(x, y)


d_cid = fig.canvas.mpl_connect('draw_event', ondraw)
bp_cid = fig.canvas.mpl_connect('button_press_event', onclick)

plt.show()