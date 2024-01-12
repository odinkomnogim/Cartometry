# To calculate the arc length, open this file in QGIS Python Console

# Before running this script, please, make sure you are using the right coordinate system
# It has to be projected (not geographic) and fit your territory of interest well

# Choose your file
line = 'your\\file\\path' 

# Divide a line so each segments is a new feature
segments = processing.run("native:explodelines", {'INPUT':line,'OUTPUT':'TEMPORARY_OUTPUT'})

# Combaine each two neighboring segments (to get 3 vertices in one feature)
vl = segments['OUTPUT']
pr = vl.dataProvider()
pr.addAttributes([QgsField("part_number", QVariant.Int)])
vl.updateFields()
exp_num = QgsExpression('CASE WHEN $id%2=0 THEN $id/2 ELSE $id/2+0.5 END')
context = QgsExpressionContext()
context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(vl))                
with edit(vl):
    for f in vl.getFeatures():
        context.setFeature(f)
        f['part_number'] = exp_num.evaluate(context)
        vl.updateFeature(f)
dissolve = processing.run("native:dissolve", {'INPUT':vl,'FIELD':['part_number'],'SEPARATE_DISJOINT':False,'OUTPUT':'TEMPORARY_OUTPUT'})

# Extract nodes from each segment
nodes = processing.run("native:extractvertices", {'INPUT':dissolve['OUTPUT'],'OUTPUT':'TEMPORARY_OUTPUT'})
features = nodes['OUTPUT'].getFeatures()
point_dict = {}
for feature in features:
    part = feature['part_number']
    if part not in point_dict:
        point_dict[part] = []
    point_dict[part].append(feature.geometry().asPoint())

# Create circles from extracted points
# And calculate acr lengths by multiplying radius and angle between points and center
centers = []
radii = []
arc_lengths = []
for part, points in point_dict.items():
    if len(points) >= 3:
        a = QgsPoint(points[0].x(), points[0].y())
        b = QgsPoint(points[1].x(), points[1].y())
        c = QgsPoint(points[2].x(), points[2].y())
        circle = QgsCircle.from3Points(a,b,c)
        center = circle.center()
        centers.append(center)
        radius = circle.radius()
        radii.append(radius)
        angle = QgsGeometryUtils.angleBetweenThreePoints(a.x(), a.y(), center.x(), center.y(), c.x(), c.y())
        if angle <3.1415926535:
            length = radius*angle
        else:
            length = radius*(2*3.1415926535-angle)
        arc_lengths.append(length)

# Create a temporary layer for circle centers
c_layer = QgsVectorLayer("Point", "point_layer", "memory")
c_layer.dataProvider().addAttributes([QgsField("Name",  QVariant.String)])
c_layer.startEditing()
c_layer.setCrs(vl.crs())
features = []
for point in centers:
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point.x(), point.y())))
    feature.setAttributes(["Point"])
    features.append(feature)
c_layer.dataProvider().addFeatures(features)
c_layer.commitChanges()

# Add radii to this temporary layer
c_layer.dataProvider().addAttributes([QgsField("radius", QVariant.Double)])
c_layer.updateFields()
with edit(c_layer):
    for i, feature in enumerate(c_layer.getFeatures()):
        if i < len(radii):
            r = radii[i]
            feature['radius'] = r
            c_layer.updateFeature(feature)
            

# Create "circle" layer by buffering center points by radii values 
circles = processing.run("native:buffer", {'INPUT':c_layer,'DISTANCE':QgsProperty.fromExpression('"radius"'),'SEGMENTS':5,'END_CAP_STYLE':0,'JOIN_STYLE':0,'MITER_LIMIT':2,'DISSOLVE':False,'OUTPUT':'TEMPORARY_OUTPUT'})
# You can later add this layer to your project and check the resulting circles if needed

# Add arc lengths as attributes to line features
three_segments = dissolve['OUTPUT']
three_segments.dataProvider().addAttributes([QgsField("arc_length", QVariant.Double)])
three_segments.updateFields()
with edit(three_segments):
    for i, feature in enumerate(three_segments.getFeatures()):
        if i < len(arc_lengths):
            l = arc_lengths[i]
            feature['arc_length'] = l
            three_segments.updateFeature(feature)

# Calculate regular lengths for last segments if they did not have a "trio"
three_segments.dataProvider().addAttributes([QgsField("length_add", QVariant.Double)])
three_segments.updateFields()
exp_num = QgsExpression('CASE WHEN "arc_length" IS NULL THEN $length ELSE NULL END')
context = QgsExpressionContext()
context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(three_segments))                
with edit(three_segments):
    for f in three_segments.getFeatures():
        context.setFeature(f)
        f['length_add'] = exp_num.evaluate(context)
        three_segments.updateFeature(f)

# Sum all arc lengths with one extra secments (if there are any)
total_arc_length = three_segments.aggregate(QgsAggregateCalculator.Sum, 'arc_length')
total_length_add = three_segments.aggregate(QgsAggregateCalculator.Sum, 'length_add')
total_length = total_arc_length[0] + total_length_add[0]
print ('Arc length:', "{:.{}f}".format(total_length, 0), 'm')

# Delete auxiliary fields that were used for total arc length calculation
with edit(three_segments):
    length_add = three_segments.fields().indexFromName('length_add')
    three_segments.dataProvider().deleteAttributes([length_add])
three_segments.updateFields()

# Calculate the regular length (a distance between vertices)
# And find the total value for comparison 
three_segments.dataProvider().addAttributes([QgsField("seg_length", QVariant.Double)])
three_segments.updateFields()
exp_num = QgsExpression('$length')
context = QgsExpressionContext()
context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(three_segments))                
with edit(three_segments):
    for f in three_segments.getFeatures():
        context.setFeature(f)
        f['seg_length'] = exp_num.evaluate(context)
        three_segments.updateFeature(f)
total_segments_length = three_segments.aggregate(QgsAggregateCalculator.Sum, 'seg_length')
print ('Segments length:', "{:.{}f}".format(total_segments_length[0], 0), 'm')

# Total lengths are now printed!

# Add a layer with calculated segments length, if needed
QgsProject.instance().addMapLayer(three_segments)