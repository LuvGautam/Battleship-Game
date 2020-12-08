from PIL import Image
from PIL import ImageOps
import os
import os.path
from string import digits
from pathlib import Path

#Path('/root/dir/sub/file.ext').stem

#s = 'abc123def456ghi789zero0'
#remove_digits = str.maketrans('', '', digits)
#res = s.translate(remove_digits)
''' 
remove_digits = str.maketrans('', '', digits)
num = (n for n in list('123456789'))

for filename in os.listdir(r".\resources\images\2590147-space-war\2590147-space-war\png"):
    if Path(r".\resources\images\2590147-space-war\2590147-space-war\png\\"+filename).is_file():
        dst = ".\\resources\\images\\2590147-space-war\\2590147-space-war\\png\\New folder\\" \
              + Path(filename).stem.translate(remove_digits).lstrip('-') \
              + '100.png'
        src = ".\\resources\\images\\2590147-space-war\\2590147-space-war\\png\\" \
              + filename

        im = Image.open(src)
        im = im.resize((100, 100))

        if Path(dst).is_file():
            dst = ".\\resources\\images\\2590147-space-war\\2590147-space-war\\png\\New folder\\" \
                  +Path(dst).stem + next(num) + '.png'
            
        im.save(dst, format="PNG")

print('done')
'''

'''
#Image resizing
#path = r'F:\PYTHON\battleship_game\resources\images\bullet\missile-explosion'
#files = ((os.path.join(path, file),file) for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)))
src = r'F:\PYTHON\battleship_game\resources\images\bullet\missile-explosion\explosion.png'
i = 1
for h,w in zip(range(45, 1081, 45), range(80, 1921, 80)):
    #src = 'F:\\PYTHON\\battleship_game\\resources\\images\\background-objects\\'+img
    im = Image.open(src)

    im = im.resize((w, h))

    dst = fr'F:\PYTHON\battleship_game\resources\images\bullet\missile-explosion\explosion{i}.png'
    #os.path.join(path, file[:len(file)-4]+'(80).png')
    #print(dst)

    im.save(dst, format="PNG")
    i += 1
'''


src = r'F:\PYTHON\battleship_game\resources\images\how-to\life-fill.png'
im = Image.open(src)

im = im.resize((72, 72))

dst = r'F:\PYTHON\battleship_game\resources\images\how-to\life72.png'

im.save(dst, format="PNG")


#Grayscaling
if False:
    img = Image.open('image.png').convert('LA')
    img.save('greyscale.png')

    #OR

     
    im1 = Image.open(r"C:\Users\System-Pc\Desktop\a.JPG") 
    im2 = ImageOps.grayscale(im1)   

'''
#Inverting colors
image = Image.open('your_image.png')
if image.mode == 'RGBA':
    r,g,b,a = image.split()
    rgb_image = Image.merge('RGB', (r,g,b))

    inverted_image = ImageOps.invert(rgb_image)

    r2,g2,b2 = inverted_image.split()

    final_transparent_image = Image.merge('RGBA', (r2,g2,b2,a))

    final_transparent_image.save('new_file.png')

else:
    inverted_image = ImageOps.invert(image)
    inverted_image.save('new_name.png')
'''

'''
#Cropping image
im = Image.open(r"F:\PYTHON\battleship_game\resources\images\background\background.png")

# The crop method from the Image module takes four coordinates as input.
# The right can also be represented as (left+width)
# and lower can be represented as (upper+height).
(left, upper, right, lower) = (100, 100, 1636, 964)

# Here the image "im" is cropped and assigned to new variable im_crop
im_crop = im.crop((left, upper, right, lower))
im_crop.save(r"F:\PYTHON\battleship_game\resources\images\background\background864.png")
'''

'''
#Rotating image
im = Image.open(r"F:\PYTHON\battleship_game\resources\images\enemy\minus32.png")

# Rotate the image by 90 degrees counter clockwise
theta = 90
# Angle is in degrees counter clockwise
im_rotated = im.rotate(angle=theta)

im_rotated.save(r"F:\PYTHON\battleship_game\resources\images\enemy\minus(90)32.png")
'''


#im.show()
