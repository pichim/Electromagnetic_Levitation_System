#%%
import numpy as np
import matplotlib.pyplot as plt
import imageio.v3 as iio
from PIL import Image           
import cv2 as cv
import os, sys
from skimage import exposure, io

#print(os.getcwd())
os.chdir(r'C:\Users\hanne\OneDrive - ZHAW\Dokumente\!_ZHAW\09_PA\15_Raspberry_Pi\Sphere_detection')

#%%
img1 = iio.imread("pics/sphere.jpg")
print('imageio:')
print(img1.shape)  # (300, 451, 3)
print(img1.size)
print(img1.dtype)
print(type(img1))
plt.figure(1)
plt.imshow(img1, cmap='gray')
plt.axis('off')


# %% calculate histogram entries

plt.figure(2)
plt.title('matplotlib histogram')
plt.hist(img1.flatten(), bins=256)
plt.xlabel('brightness value')
plt.ylabel('number of value')



# %% 2. Gamma correction
img1 = img1.astype(float)/255.0
y = 0.5
img1_gamma = img1**y
img1_skimage = exposure.adjust_gamma(img1, gamma=y)

plt.figure(5)
plt.title('original image')
plt.imshow(img2, cmap='gray')
plt.figure(6)
plt.title(f'with gamma ={y}')
plt.imshow(img2_gamma, cmap='gray')
plt.figure(7)
plt.title(f'with gamma ={y} scikit')
plt.imshow(img2_skimage, cmap='gray')


#%%
img3 = iio.imread("pics/ctSkull.tif")
img3 = img3.astype(float)/255.0
y = 1.5
img3_gamma = img1**y

plt.figure(7)
plt.title('original image')
plt.imshow(img3, cmap='gray')
plt.figure(8)
plt.title(f'with gamma ={y}')
plt.imshow(img3_gamma, cmap='gray')


# %% 3 Contrast Enhancement by Histogram Equalization
img2 = img1
hist2 = np.zeros(256)
for i in range(img2.shape[0]):
    for j in range(img2.shape[1]):
        hist2[img2[i,j]] = hist2[img2[i,j]] + 1

hist2_eq = np.zeros(256)
for n in range(256):
    hist2_eq[n] = (hist2_eq[n-1] + hist2[n]) 

hist2_eq /= max(hist2_eq)
img2_eq = img2.copy()
for i in range(img2.shape[0]):
    for j in range(img2.shape[1]):
        img2_eq[i,j] = img2_eq[i,j] * hist2_eq[img2_eq[i,j]]


plt.figure(10)
plt.title('histogram and cdf scaled')
plt.plot(hist2/max(hist2), label='histogram')
plt.plot(hist2_eq, label='histogram_equalisation')
plt.xlabel('brightness value')
plt.ylabel('number of value')

# Create figure with 1 row and 2 columns
fig, axes = plt.subplots(1, 2, figsize=(10, 5))

# Left image
axes[0].imshow(img2, cmap="gray")  # cmap='gray' is required for grayscale images
axes[0].set_title("Original")
axes[0].axis("off")                # Hide axis ticks and coordinates

# Right image
axes[1].imshow(img2_eq, cmap="gray")
axes[1].set_title("contrast equalized")
axes[1].axis("off")

plt.tight_layout()
plt.show()
# %%
