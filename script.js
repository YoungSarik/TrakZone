function generateQRCode() {
    const eventData = "Sarvar Jabborov-Roadshow"; // Example: Replace with actual data
    const qrImage = document.getElementById("qrCode");

    fetch(`http://127.0.0.1:5000/generate_qr?data=${encodeURIComponent(eventData)}`)
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
