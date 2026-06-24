let stream = null;
let currentType = "clockin";

function setCaptureType(type) {
    currentType = type;
}
async function openCamera(type) {

    currentType = type;

    try {

        stream = await navigator.mediaDevices.getUserMedia({
            video: true
        });

        const video = document.getElementById("video");

        video.srcObject = stream;

        document.getElementById("cameraModal").style.display = "block";

    } catch (err) {
        alert("Camera permission denied");
        console.error(err);
    }
}

function closeCamera() {

    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }

    document.getElementById("cameraModal").style.display = "none";
}

async function capturePhoto() {

    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");

    ctx.drawImage(video, 0, 0);

    canvas.toBlob(async function(blob) {

        await uploadAttendance(blob, currentType);

        closeCamera();   // 👈 IMPORTANT FIX HERE

    }, "image/jpeg", 0.9);
}

async function uploadClockIn(blob) {

    let formData = new FormData();
ß
    formData.append("photo", blob, "clockin.jpg");

    const response = await fetch("/attendance/clockin", {
        method: "POST",
        body: formData
    });

    const result = await response.json();
     window.location.reload();
    alert(result.message || "Clocked In Successfully");
}

let isUploading = false;

async function uploadAttendance(blob, type) {

    if (isUploading) return;

    isUploading = true;

    try {

        let formData = new FormData();
        formData.append("photo", blob, "photo.jpg");

        const response = await fetch(`/attendance/${type}`, {
            method: "POST",
            body: formData
        });

        let result;

        try {
            result = await response.json();
        } catch (e) {
            throw new Error("Invalid JSON response from server");
        }

        if (!response.ok) {
            throw new Error(result.message || "Server error");
        }
        window.location.reload();
        alert(result.message || "Success");

    } catch (err) {

        console.error("Upload error:", err);
        alert(err.message);

    } finally {

        isUploading = false;
    }
}