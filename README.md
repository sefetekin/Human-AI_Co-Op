# 🎮 Human-AI Co-Op: Adaptive Survival Game

A custom infinite-survival game built with **Pygame**, implementing a **dual-layer adaptive framework**:

- **Mechanical adaptation** → Dynamic Difficulty Adjustment (DDA)  
- **Experiential adaptation** → Diffusion-generated visuals + LLM commentary  

The system personalises both **how the game plays** and **how it feels**, while ensuring these layers remain independent and stable.

---

## 🧠 Key Idea

Traditional games adapt difficulty only.

This project goes further:

- 🕹️ **DDA** → adapts challenge in real time  
- 🎨 **Diffusion** → generates personalised visual environments  
- 💬 **LLM** → provides context-aware commentary  

👉 Crucially:  
Generative components improve experience **without affecting gameplay performance**

---

## 🚀 Installation & Running

### 1. Gameplay (Main System)

Install:  
```bash  
pip install -r requirements.txt  
```

Run:  
```bash  
python src/main.py  
```

---

### 2. Optional: Diffusion (Generative Content)

Only needed if you want **background generation**.

Install:  
```bash  
pip install -r diffusion_requirements.txt  
pip install git+https://github.com/zengxianyu/structured-noise  
```

Setup:
- Download model weight https://huggingface.co/zengxianyu/ppd/blob/main/sd1.5-epoch%3D10-step%3D720000.ckpt
- Place them in:  
```  
models/ppd/  
```  

(Optional example inputs are also in this folder)

---

## 🎮 How to Use Generative Features

In the **player setup screen**:

- Enable:
  - Content Generation (top-left toggle)
  - Optional LLM commentary
- Provide:
  - Player preferences (mood, object, etc.)

This triggers:
- Pre-game diffusion-based background generation  
- In-game LLM commentary  

---

## ⚙️ System Overview

### 1. Dynamic Difficulty Adjustment (DDA)
- Updates once per second (not per frame)
- Uses:
  - health, kill rate, shield usage  
  - enemy density, distance, pressure  
- Produces a difficulty score in **[0,1]**
- Derived empirically through iterative tuning

---

### 2. Generative Visual Adaptation
- Uses phase-preserving diffusion  
- Maintains spatial structure while changing style  
- Runs before gameplay (no runtime lag)

---

### 3. LLM Commentary
- Generates short, context-aware lines  
- Conditioned on gameplay metrics and player preferences  
- Does not affect gameplay mechanics  

---

## 📊 Key Result

- DDA significantly improves survival time  
- Generative features:
  - do NOT change performance  
  - DO improve perceived experience  

This validates:  
Mechanical and experiential adaptation can be combined **without interference**

---

## 📁 Project Structure

```  
src/  
├── main.py  
├── game_manager.py  
├── character.py  
├── enemy.py  
├── assets/  
├── logger.py  
├── agentic_dda.py  
```  

```  
models/  
└── ppd/  
```  

---

## 🧪 Notes for Reproducibility

- Core gameplay has minimal dependencies  
- Generative pipeline is isolated  
- Ensures easier setup and stable execution  

---

## ⚠️ Important

- Diffusion requires GPU for best performance  
- If not installed, the game still runs normally  

---

## 🧠 Summary

- DDA controls challenge  
- Generative AI enhances experience  
- Both coexist without breaking gameplay  