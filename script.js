const API_URL = "http://127.0.0.1:5500"; // Change to your deployed API URL if needed

function generateQRCode() {
    const eventId = 1; // Replace this with dynamic event selection if needed
    const qrImage = document.getElementById("qrCode");

    fetch(`${API_URL}/generate_qr/${eventId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("QR Code generation failed");
            }
            return response.blob();
        })
        .then(blob => {
            const qrUrl = URL.createObjectURL(blob);
            qrImage.src = qrUrl;
        })
        .catch(error => console.error("Error:", error));
}
