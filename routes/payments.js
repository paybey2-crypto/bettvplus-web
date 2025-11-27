import express from "express";
const router = express.Router();

// Primer Stripe webhook rute
router.post("/webhook", (req, res) => {
    console.log("Stripe webhook received:", req.body);
    res.status(200).send("Webhook received");
});

export default router;

