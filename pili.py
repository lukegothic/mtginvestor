import cv2, os
import json, requests, time, threading, sys
from queue import Queue

method = cv2.TM_SQDIFF_NORMED

target_image = 'X:\\mtgcontest\\{}.jpg'.format(sys.argv[1])
# Read the images from the file
base_dir = "Y:\\Code\\mtginvestor\\output\\crops"
small_image = cv2.imread(target_image)
full_images = os.listdir(base_dir)
results = []

def do_work(id):
    sys.stdout.write("Restantes: %d   \r" % q.qsize())
    sys.stdout.flush()
    large_image = cv2.imread("{}\\{}".format(base_dir,id))
    try:
        result = cv2.matchTemplate(small_image, large_image, method)
        results.append({"k": id, "r": cv2.minMaxLoc(result)})
    except:
        result = None
   
def worker():
    while True:
        do_work(q.get())
        q.task_done()

output = "{}.results.json".format(target_image)

if not os.path.exists(output):
    q = Queue()
    for i in range(8):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
    for fi in full_images:
        q.put(fi)
    q.join()
    with open(output, "w") as f:
        json.dump(results, f, separators=(',', ':'))
else:
    with open(output) as f:
        results = json.load(f)




# minxx = 100
# minmatch = None

# for r in results:
#     if r["r"][0] < minxx:
#         minxx = r["r"][0]
#         minmatch = r["k"]
def get_min(elm):
    return elm["r"][0]

results.sort(key=get_min)

for r in range(len(results)):
    # Draw the rectangle:
    # Extract the coordinates of our best match
    MPx,MPy = results[r]["r"][2]

    # Step 2: Get the size of the template. This is the same size as the match.
    trows,tcols = small_image.shape[:2]

    large_image = cv2.imread("{}\\{}".format(base_dir,results[r]["k"])) 

    # Step 3: Draw the rectangle on large_image
    cv2.rectangle(large_image, (MPx,MPy),(MPx+tcols,MPy+trows),(0,0,255),2)
    print(results[r]["k"])
    # Display the original image with the rectangle around the match.
    cv2.imshow('output',large_image)

    # The image is only displayed if we call this
    cv2.waitKey(0)    