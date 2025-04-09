import cv2

# Path to your image
image_path = "thermal_imges_for_exp\CH01.jpeg"
image = cv2.imread(image_path)
clone = image.copy()

ref_points = []
drawing = False
ix, iy = -1, -1

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, ref_points

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        cv2.rectangle(image, (ix, iy), (x, y), (0, 255, 0), 2)
        w, h = x - ix, y - iy
        ref_points.append({"x": min(ix, x), "y": min(iy, y), "width": abs(w), "height": abs(h)})
        print(f"Box: x={min(ix, x)}, y={min(iy, y)}, width={abs(w)}, height={abs(h)}")

# Set up window and mouse callback
cv2.namedWindow("Select Regions")
cv2.setMouseCallback("Select Regions", draw_rectangle)

print("🖱️ Click and drag to draw boxes. Press [ESC] to finish.\n")

while True:
    cv2.imshow("Select Regions", image)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC to exit
        break

cv2.destroyAllWindows()

# Print all regions
print("\n📦 Final extracted regions:")
for i, box in enumerate(ref_points):
    print(f"Region {i + 1}: {box}")
