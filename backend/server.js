import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import bodyParser from "body-parser";

import deviceRoutes from "./routes/devices.js";
import paymentRoutes from "./routes/payments.js";
import adminRoutes from "./routes/admin.js";

dotenv.config();

const app = express();

app.use(cors());
app.use(express.json());

// Stripe webhook mora RAW
app.use("/payments/webhook", paymentRoutes);

// Ostali JSON
app.use(bodyParser.json());

app.use("/devices", deviceRoutes);
app.use("/admin", adminRoutes);

app.get("/", (req, res) => {
    res.send("Bet TV Plus Backend Running");
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log("Server running on port", PORT));

