# Line measurment using acrs
This script measures lines in QGIS using circular arcs. 

## Why?
Meandering lines in nature (for example, rivers) are not exaxtly polygonal chains, as they are portrayed in GIS. 
So, if we measure them in a standard way by adding the lengths of all the segments, we may lose the length of the bends.
By calculating the length of the circle arc as the product of the *radius* of the circle formed by each three points of the line and the angle between first point, circle center and the last point (in radians), we can obtain additional information. 
![explanation](https://github.com/odinkomnogim/Cartometry/blob/main/calculation_principle.png?raw=true)

## Usage
To calculate the arc length, open 'cartometry.py' in QGIS Python Console.
Before running this script, please, make sure you are using the right coordinate system.
It has to be projected (not geographic) and fit your territory of interest well.
