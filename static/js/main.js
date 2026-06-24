
async function clockIn() {
    openCamera();
}

async function startBreak(){
    await fetch("/start-break");
    alert("Break Started");
    
    window.location.reload();
}

async function endBreak(){
    await fetch("/end-break");
    alert("Break Ended");
    window.location.reload();
}

function getAttendanceData() {

    const dataElement = document.getElementById("attendance-data");

    if (!dataElement) return {};

    try {
        return JSON.parse(dataElement.textContent);
    } catch (e) {
        console.error("Invalid attendance data", e);
        return {};
    }
}

function formatTime(dt) {

    if (!dt) return "";

    let date = new Date(dt);

    return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}

async function clockOut(){

    openCamera("clockout");
    alert("Clocked Out");
}

function updateReminder(attendance) {

    const msg = document.getElementById("reminder-message");

    // Not logged in / no attendance record
    if (!attendance || !attendance.clock_in_time) {
        msg.innerText = "Please clock in to start your shift";
        return;
    }

    // On break
    if (attendance.status === "On Break") {
        msg.innerText = "You are on break. Please resume after break";
        return;
    }

    // Completed
    if (attendance.status === "Completed") {
        msg.innerText = "Shift completed. Please clock in for a new shift";
        return;
    }

    // Working
    if (attendance.status === "Working") {
       msg.innerText =
        "You are clocked in at " +
        attendance.clock_in_time;
        return;
    }
}
 
function checkClockOutReminder(){

    let now = new Date();

    if(now.getHours() === 16){

        document.getElementById(
            "reminder-message"
        ).innerHTML =
            "Please clock out before leaving.";

        if(Notification.permission === "granted"){

            new Notification(
                "Clock Out Reminder",
                {
                    body:
                    "Please clock out before leaving."
                }
            );
        }
    }
}

if("Notification" in window){

    Notification.requestPermission();
}

setInterval(
    checkClockOutReminder,
    60000
);

checkClockOutReminder();

document.addEventListener("DOMContentLoaded", function () {

    const attendance = getAttendanceData();

    updateReminder(attendance);

});

