function payYear() {
    window.location.href = "https://tvoj-stripe-link-za-godisnju-pretplatu.com";
}

function payLifetime() {
    window.location.href = "https://tvoj-stripe-link-za-lifetime.com";
}

document.getElementById("activateForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const mac = document.getElementById("mac").value;

    const res = await fetch("https://tvoj-render-api.onrender.com/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mac })
    });

    const data = await res.json();
    document.getElementById("result").innerText = data.message;
});

