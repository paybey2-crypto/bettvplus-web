import express from "express";
const router = express.Router();

// Primer rute
router.get("/", (req, res) => {
    res.json({ message: "Devices route" });
});

export default router;

