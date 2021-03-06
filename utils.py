import numpy as np
import matplotlib.pyplot as plt
import cv2
import os, random
from scipy import interpolate
from sklearn.utils import shuffle
import pickle

DIM = 28

class signal_processor:

    def scale(self,example):
        #Scales the coordinate system to 28 by 28

        X=example[:,1]
        Y=example[:,0]

        #Resize to 104 pixels
        X=X-np.min(X)
        Y=Y-np.min(Y)

        delta=np.max([np.max(np.abs(X)),np.max(np.abs(Y))])
        if delta != 0:
            X=X.astype(float)/delta*(DIM-1)
            Y=Y.astype(float)/delta*(DIM-1)

        example[:,1],example[:,0]=X,Y

        scaled_example=np.zeros(example.shape)
        scaled_example[:,1],scaled_example[:,0],scaled_example[:,2]=X,Y,example[:,2]

        return scaled_example
    def get_raw_image(self,example):
        #Creates Raw Image from X and Y

        X=example[:,1]
        Y=example[:,0]

        img=np.zeros((DIM,DIM))

        for i in range(X.shape[0]):
            if example[i,2]==0:
                img[int(X[i]),int(Y[i])]=1

        return img
    def fit_to_box(self,img):
        #The image is compressed so that it fits the smallest possible box

        left,right,top,bot=DIM,0,DIM,0

        #Find bounds on X

        #Left bound
        for row in range(DIM):
            for i in range(DIM):
                if img[row,i]==1:
                    if i<left:
                        left=i

        #Right bound
        for row in range(DIM):
            for i in range(DIM-1,-1,-1):
                if img[row,i]==1:
                    if i>right:
                        right=i

        #Left bound
        for col in range(DIM):
            for i in range(DIM):
                if img[i,col]==1:
                    if i<top:
                        top=i

        #Right bound
        for col in range(DIM):
            for i in range(DIM-1,-1,-1):
                if img[i,col]==1:
                    if i>bot:
                        bot=i

        new_img=img[top:bot+2,left:right+2]

        return new_img
    def linear_interpolate(self, example, img):

        cnt=0
        for i in range(example.shape[0]-1):

            #If pen is on the paper do interpolation
            if int(round(example[i,2]))==0:
                cnt+=1

                X_1,Y_1=int(round(example[i,1])),int(round(example[i,0]))
                X_2,Y_2=int(round(example[i+1,1])),int(round(example[i+1,0]))

                #print("({},{})->({},{})".format(X_1,Y_1,X_2,Y_2))

                Y_min,Y_max=min(Y_1,Y_2),max(Y_1,Y_2)
                X_min,X_max=min(X_1,X_2),max(X_1,X_2)


                #Check if the line is vertical
                if X_min==X_max:
                    #print('Vertical')
                    for y in range(Y_min,Y_max+1):
                        img[X_min,y]=1

                elif Y_min==Y_max: #The line is horizontal
                    #print('Horizontal')
                    for x in range(X_min,X_max+1):
                        img[x,Y_min]=1

                else: #Line is at angle

                    #print('Line')
                    k = (Y_1-Y_2)/(X_1-X_2)
                    n = Y_1-k*X_1

                    if X_max-X_min > Y_max - Y_min:
                        painted=0
                        x=X_min
                        while x<X_max:
                            x+=1
                            y=k*x+n

                            img[int(round(x)),int(round(y))]=1

                    else:
                        painted=0
                        y=Y_min
                        while y<Y_max:
                            y+=1
                            x=(y-n)/k

                            img[int(round(x)),int(round(y))]=1

            else: #Do nothing
                pass
        #print(cnt)
        return img
    def is_contained(self,x,y,img):
        if x<0 or y<0 or x>=img.shape[0] or y>=img.shape[1]:
            return False
        return True
    def apply_mask(self,img, mask):

        if mask.shape[0]%2==0 or mask.shape[1]%2==0:
            print('Mask dimensions should be odd!')

        else:
            new_img=np.copy(img)
            neighbours=[]

            Xc=int(mask.shape[0]/2)
            Yc=int(mask.shape[1]/2)

            for x in range(mask.shape[0]):
                for y in range(mask.shape[1]):
                    if mask[x,y]==1:
                        neighbours.append((x-Xc,y-Yc))

            #print(neighbours)

            for x in range(img.shape[0]):
                for y in range(img.shape[1]):
                    if img[x,y]==1:
                        for dx,dy in neighbours:
                            if self.is_contained(x+dx,y+dy,img):
                                new_img[x+dx,y+dy]=1

            return new_img
    def get_image(self,signal):
        signal=self.scale(signal)

        #Get image of points in shape 28x28
        img=self.get_raw_image(signal)
        #Connect points
        img=self.linear_interpolate(signal,img)
        #Apply mask
        #img=self.apply_mask(img,np.array([[0,0,1,0,0],[0,1,1,1,0],[1,1,1,1,1],[0,1,1,1,0],[0,0,1,0,0]]))
        img = self.apply_mask(img,np.array([[0,1,0],[1,1,1],[0,1,0]]))
        #Remove unnecessary parts
        img=self.fit_to_box(img)

        #Padding image
        height, width = img.shape
        pad_h = (DIM - height) // 2 + 5
        pad_w = (DIM - width) // 2 + 5

        img = np.pad(img, [(pad_h, pad_h), (pad_w, pad_w)], 'constant', constant_values = (0,0))

        img = cv2.resize(img, (28,28))
        img = (img>0.5)*1

        return img
