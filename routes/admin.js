import express from "express";
const router = express.Router();

// Primer admin rute
router.get("/", (req, res) => {
    res.json({ message: "Admin route" });
});

export default router;

