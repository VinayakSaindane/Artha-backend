const { GoogleGenerativeAI } = require("@google/generative-ai");
require('dotenv').config();

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

async function testModels() {
    try {
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
        const result = await model.generateContent("test");
        console.log("Gemini 1.5 Flash works!");
    } catch (e) {
        console.error("Gemini 1.5 Flash failed:", e.message);
    }

    try {
        const model = genAI.getGenerativeModel({ model: "gemini-pro" });
        const result = await model.generateContent("test");
        console.log("Gemini Pro works!");
    } catch (e) {
        console.error("Gemini Pro failed:", e.message);
    }
}

testModels();
