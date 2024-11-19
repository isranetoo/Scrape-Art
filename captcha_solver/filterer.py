
from io import BytesIO

import numpy as np

from PIL import Image
from PIL import ImageFilter
from scipy.ndimage import gaussian_filter

from pylab import axes, ylabel, xlabel, subplot, draw, show, imshow
from matplotlib.widgets import Slider, Button


files = './images/'
img = "4fw64r.jpeg"
with open(f"{files}{img}", "rb") as bytes_data:
    original = Image.open(BytesIO(bytes_data.read()))


def update(val):
    th1 = float(smth1.val)
    th2 = float(smth2.val)
    sig1 = float(smsig1.val)
    sig2 = float(smsig2.val)

    black_and_white = original.convert("L")  # converting to black and white
    first_threshold = black_and_white.point(lambda p: p > th1 and 255)
    blur = np.array(first_threshold)  # create an image array
    blurred = gaussian_filter(blur, sigma=sig1)
    blurred = Image.fromarray(blurred)
    final = blurred.point(lambda p: p > th2 and 255)
    final = final.filter(ImageFilter.EDGE_ENHANCE_MORE)
    final = final.filter(ImageFilter.SHARPEN)

    blur2 = np.array(final)  # create an image array
    blurred2 = gaussian_filter(blur2, sigma=sig2)
    blurred2 = Image.fromarray(blurred2)
    final2 = blurred2.point(lambda p: p > th2 and 255)
    final2 = final2.filter(ImageFilter.EDGE_ENHANCE_MORE)
    final2 = final2.filter(ImageFilter.SHARPEN)

    l.set_data(final2)
    draw()

def reset(event):
    smth1.reset()
    smth2.reset()
    smsig1.reset()
    smsig2.reset()

ax = subplot(111)
ax.grid(True)

ini_th1 = 137
ini_th2 = 143
ini_sig1 = 1.5
ini_sig2 = 1.0

l = imshow(original)
xlabel("Distancia")
ylabel("Altura")

axth1  = axes([0.25, 0.20, 0.65, 0.03])
axth2  = axes([0.25, 0.15, 0.65, 0.03])
axsig1  = axes([0.25, 0.10, 0.65, 0.03])
axsig2  = axes([0.25, 0.05, 0.65, 0.03])

smth1 = Slider(axth1, 'TH1',    ini_th1 * 0.5,  ini_th1 * 2,  valinit=ini_th1)
smth2 = Slider(axth2, 'TH2',    ini_th2 * 0.5,  ini_th2 * 2,  valinit=ini_th2)
smsig1 = Slider(axsig1, 'SIG1', ini_sig1 * 0.5, ini_sig1 * 2, valinit=ini_sig1)
smsig2 = Slider(axsig2, 'SIG2', ini_sig2 * 0.5, ini_sig1 * 2, valinit=ini_sig2)

smth1.on_changed(update)
smth2.on_changed(update)
smsig1.on_changed(update)
smsig2.on_changed(update)

resetax = axes([ini_th1, ini_th2, ini_sig1, ini_sig2])

button = Button(resetax, 'Reset', hovercolor='0.975')
button.on_clicked(reset)
show()
