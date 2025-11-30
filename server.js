const express = require("express");
const app = express();
const path = require("path");

app.use(express.json());
app.use(express.static("public"));

const USER = "admin";
const PASS = "1234";

app.post("/login", (req, res) => {
    const { username, password } = req.body;

    if (username === USER && password === PASS) {
        return res.json({ message: "Login successful!" });
    }

    res.json({ message: "Invalid username or password." });
});

app.listen(3000, () => console.log("Server running on port 3000"));
