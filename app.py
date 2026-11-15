import os
import http.server
import socketserver
import logging

PORT = int(os.environ.get("PORT", 8000))
HOST = "0.0.0.0"

logging.basicConfig(level=logging.INFO)

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>DSLR Frame Extractor</title>

<script src="https://cdn.tailwindcss.com"></script>

<style>
body {
    background: #020617;
    color: white;
    font-family: Arial, sans-serif;
}

.card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 18px;
    overflow: hidden;
}

button, input {
    transition: 0.2s;
}

.frame-image {
    width: 100%;
    aspect-ratio: 16/9;
    object-fit: contain;
    background: #020617;
}

.progress-bar {
    height: 8px;
    background: #1e293b;
    border-radius: 20px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg,#06b6d4,#6366f1);
    transition: width 0.2s;
}
</style>
</head>

<body class="min-h-screen">

<div class="max-w-6xl mx-auto px-4 py-8">

<header class="text-center mb-10">

<div class="inline-block bg-emerald-950 text-emerald-400
px-4 py-2 rounded-full text-xs mb-4">

MG SHANKAR TECH • FRAME EXTRACTOR

</div>

<h1 class="text-3xl md:text-5xl font-extrabold
bg-gradient-to-r from-cyan-400 to-indigo-400
bg-clip-text text-transparent">

🎬 Video to DSLR Frame Extractor

</h1>

<p class="text-slate-400 mt-4">

Extract high-quality photographs from your videos.

</p>

</header>


<!-- CONTROL PANEL -->

<div class="card p-6 md:p-8 mb-8">

<h2 class="text-xl font-bold mb-6">

⚙️ Frame Extraction Settings

</h2>

<div class="grid md:grid-cols-2 gap-6">

<div>

<label class="block mb-3 text-sm text-slate-300">

📹 Select Video

</label>

<input
type="file"
id="videoInput"
accept="video/*"
class="w-full text-sm bg-slate-950 p-3 rounded-xl border border-slate-700"
>

</div>


<div>

<label class="block mb-3 text-sm text-slate-300">

⏱️ Capture Interval (Seconds)

</label>

<input
type="number"
id="intervalInput"
value="1"
min="0.1"
max="60"
step="0.1"
class="w-full bg-slate-950 p-3 rounded-xl border border-slate-700"
>

</div>

</div>


<div class="mt-6">

<label class="flex items-center gap-3 text-sm">

<input type="checkbox" id="enhanceInput" checked>

Enable Image Enhancement

</label>

<p class="text-xs text-slate-500 mt-2">

Enhancement adjusts contrast and color. It cannot fully
restore motion blur or missing image details.

</p>

</div>


<div class="mt-8 text-center">

<button
id="extractButton"
onclick="extractFrames()"
class="bg-cyan-500 hover:bg-cyan-400 text-slate-950
font-bold px-10 py-4 rounded-xl">

🚀 Extract Frames

</button>

</div>

</div>


<!-- VIDEO PREVIEW -->

<div class="card p-4 mb-8">

<h2 class="font-bold mb-4">🎥 Video Preview</h2>

<video
id="videoElement"
controls
playsinline
class="w-full max-h-96 bg-black rounded-xl">

</video>

</div>


<!-- PROGRESS -->

<div class="mb-8">

<div id="statusText"
class="text-center text-cyan-400 mb-4">

Waiting for video...

</div>

<div class="progress-bar">

<div id="progressFill" class="progress-fill"></div>

</div>

</div>


<!-- GALLERY -->

<div>

<div class="flex justify-between items-center mb-6">

<h2 class="text-xl font-bold">

✨ Extracted Gallery

</h2>

<span id="frameCount"
class="bg-cyan-950 text-cyan-400 px-4 py-2 rounded-full text-sm">

0 Shots

</span>

</div>


<div class="flex gap-3 mb-6 flex-wrap">

<button
onclick="downloadAll()"
class="bg-emerald-600 hover:bg-emerald-500 px-5 py-3 rounded-xl font-bold">

⬇ Download All

</button>

<button
onclick="clearGallery()"
class="bg-red-600 hover:bg-red-500 px-5 py-3 rounded-xl font-bold">

🗑 Clear Gallery

</button>

</div>


<div
id="galleryGrid"
class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">

</div>

</div>


<footer class="text-center text-slate-500 text-sm mt-16">

<p>Developed by MG Shankar Tech</p>

<p class="mt-2">Video to DSLR Frame Extractor</p>

</footer>

</div>


<canvas id="canvas" hidden></canvas>


<script>

const video = document.getElementById("videoElement");

const canvas = document.getElementById("canvas");

const ctx = canvas.getContext("2d");

let frames = [];

let busy = false;

let videoURL = null;


const statusText = document.getElementById("statusText");

const progressFill = document.getElementById("progressFill");

const gallery = document.getElementById("galleryGrid");


function setStatus(message) {

    statusText.textContent = message;

}


function waitForEvent(element, eventName) {

    return new Promise((resolve, reject) => {

        const onSuccess = () => {
            cleanup();
            resolve();
        };

        const onError = () => {
            cleanup();
            reject(new Error("Video loading failed"));
        };

        function cleanup() {
            element.removeEventListener(eventName, onSuccess);
            element.removeEventListener("error", onError);
        }

        element.addEventListener(eventName, onSuccess, {once:true});

        element.addEventListener("error", onError, {once:true});

    });

}


document.getElementById("videoInput").addEventListener("change", function() {

    const file = this.files[0];

    if (!file) return;

    if (videoURL) URL.revokeObjectURL(videoURL);

    videoURL = URL.createObjectURL(file);

    video.src = videoURL;

    video.load();

    setStatus("Video selected successfully!");

});


async function extractFrames() {

    if (busy) return;

    const file = document.getElementById("videoInput").files[0];

    const interval = Number(
        document.getElementById("intervalInput").value
    );

    const enhance = document.getElementById("enhanceInput").checked;

    if (!file) {

        alert("Please select a video!");

        return;

    }

    if (!Number.isFinite(interval) || interval < 0.1 || interval > 60) {

        alert("Please enter an interval between 0.1 and 60 seconds.");

        return;

    }

    busy = true;

    const button = document.getElementById("extractButton");

    button.disabled = true;

    button.textContent = "Processing...";

    clearGallery();

    try {

        if (!video.src || !videoURL) {

            throw new Error("Please select a valid video.");

        }

        if (video.readyState < 1) {

            const metadataPromise = waitForEvent(video, "loadedmetadata");

            await metadataPromise;

        }

        const duration = video.duration;

        if (!Number.isFinite(duration) || duration <= 0) {

            throw new Error("Invalid video duration.");

        }

        if (!video.videoWidth || !video.videoHeight) {

            throw new Error("Video dimensions unavailable.");

        }

        const totalFrames = Math.min(
            300,
            Math.ceil(duration / interval)
        );

        canvas.width = video.videoWidth;

        canvas.height = video.videoHeight;

        let count = 0;

        for (let i = 0; i < totalFrames; i++) {

            const currentTime = Math.min(i * interval, duration);

            const seekPromise = waitForEvent(video, "seeked");

            video.currentTime = currentTime;

            await seekPromise;

            ctx.filter = enhance
                ? "contrast(1.10) saturate(1.08) brightness(1.02)"
                : "none";

            ctx.drawImage(
                video,
                0,
                0,
                canvas.width,
                canvas.height
            );

            ctx.filter = "none";

            const blob = await new Promise(resolve => {

                canvas.toBlob(resolve, "image/jpeg", 0.95);

            });

            if (!blob) continue;

            const imageURL = URL.createObjectURL(blob);

            count++;

            frames.push({

                url: imageURL,

                blob: blob,

                time: currentTime,

                name: "MGShankar_Frame_" + count + ".jpg"

            });

            createCard(frames[frames.length - 1], count);

            const progress = Math.round(
                ((i + 1) / totalFrames) * 100
            );

            progressFill.style.width = progress + "%";

            document.getElementById("frameCount").textContent =
                count + " Shots";

            setStatus(
                "Extracting frames: " + progress + "%"
            );

            // Browser को UI अपडेट करने का समय दें।
            await new Promise(resolve => setTimeout(resolve, 0));

        }

        setStatus(
            "Successfully extracted " + count + " frames! 🎉"
        );

    }

    catch(error) {

        console.error(error);

        setStatus("Error: " + error.message);

        alert(error.message);

    }

    finally {

        busy = false;

        button.disabled = false;

        button.textContent = "🚀 Extract Frames";

    }

}


function createCard(frame, number) {

    const card = document.createElement("div");

    card.className = "card";

    const img = document.createElement("img");

    img.src = frame.url;

    img.className = "frame-image";

    img.alt = "Extracted Frame " + number;

    const info = document.createElement("div");

    info.className = "p-4";

    const title = document.createElement("p");

    title.className = "text-sm text-slate-300 mb-3";

    title.textContent =
        "Frame " + number + " • " + frame.time.toFixed(2) + "s";

    const download = document.createElement("a");

    download.href = frame.url;

    download.download = frame.name;

    download.textContent = "⬇ Save Photo";

    download.className =
        "block text-center bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold p-3 rounded-xl";

    info.appendChild(title);

    info.appendChild(download);

    card.appendChild(img);

    card.appendChild(info);

    gallery.appendChild(card);

}


function downloadAll() {

    if (frames.length === 0) {

        alert("No frames available!");

        return;

    }

    frames.forEach((frame, index) => {

        setTimeout(() => {

            const link = document.createElement("a");

            link.href = frame.url;

            link.download = frame.name;

            document.body.appendChild(link);

            link.click();

            link.remove();

        }, index * 400);

    });

}


function clearGallery() {

    frames.forEach(frame => {

        URL.revokeObjectURL(frame.url);

    });

    frames = [];

    gallery.innerHTML = "";

    document.getElementById("frameCount").textContent = "0 Shots";

    progressFill.style.width = "0%";

}

</script>

</body>
</html>
"""


class CustomHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path not in ("/", "/index.html"):

            self.send_error(404)

            return

        content = HTML_CONTENT.encode("utf-8")

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(content))
        )

        self.send_header(
            "Cache-Control",
            "no-store"
        )

        self.end_headers()

        self.wfile.write(content)

    def log_message(self, format, *args):

        logging.info("%s - %s", self.address_string(), format % args)


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):

    daemon_threads = True

    allow_reuse_address = True


if __name__ == "__main__":

    with Server((HOST, PORT), CustomHandler) as server:

        print(f"Server running at http://{HOST}:{PORT}")

        server.serve_forever()
