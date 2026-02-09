#!/usr/bin/env python3
"""
🧠 NEMESIS - IA Locale CLI
Assistant IA tout-en-un, 100% local, rapide et extensible
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from tools.rag_memory import RAGMemory

# Configuration
MEMORY_FILE = "memory.json"
DEFAULT_MODEL = "qwen2.5:7b"
CODER_MODEL = "deepseek-coder:6.7b"
MAX_MEMORY_CHARS = 20000  # Limite de caractères pour le contexte
SUMMARY_THRESHOLD = 0.7   # Seuil pour déclencher le résumé (70%)
RAG_RESULT_COUNT = 3      # Nombre de résultats RAG à injecter

# Modes disponibles
MODES = {
    "default": {"name": "Mode par défaut", "model": DEFAULT_MODEL, "desc": "Polyvalent et équilibré"},
    "dev": {"name": "Mode développeur", "model": CODER_MODEL, "desc": "Expert en code (DeepSeek)"},
    "debug": {"name": "Mode debug", "model": CODER_MODEL, "desc": "Chasseur de bugs (DeepSeek)"},
    "study": {"name": "Mode étude", "model": DEFAULT_MODEL, "desc": "Tuteur pédagogique"},
    "architect": {"name": "Mode architecte", "model": CODER_MODEL, "desc": "Architecture & Design"}
}

# État global
current_mode = "default"
rag_memory = None

def get_project_root():
    """Détecte la racine du projet Git actuel"""
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], 
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return root
    except subprocess.CalledProcessError:
        return "global"

def get_timestamp():
    """Retourne un timestamp formaté"""
    from datetime import datetime
    return datetime.now().isoformat()

def load_memory_structure():
    """Charge la structure complète de la mémoire"""
    if not os.path.exists(MEMORY_FILE):
        return {"global": [], "projects": {}}
    
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Migration si nécessaire
            if isinstance(data, list):
                new_data = {
                    "global": [{"role": "system", "content": "Archives migration", "timestamp": get_timestamp()}], 
                    "projects": {"legacy_archive": data}
                }
                save_memory_structure(new_data)
                return new_data
            return data
    except json.JSONDecodeError:
        return {"global": [], "projects": {}}

def save_memory_structure(data):
    """Sauvegarde la structure complète de la mémoire"""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_current_context_memory(memory_data, project_root):
    """Récupère la liste des messages pour le contexte actuel"""
    if project_root == "global":
        return memory_data["global"]
    if project_root not in memory_data["projects"]:
        memory_data["projects"][project_root] = []
    return memory_data["projects"][project_root]

def add_memory_entry(memory_data, project_root, role, content):
    """Ajoute une entrée à la mémoire"""
    entry = {"role": role, "content": content, "timestamp": get_timestamp()}
    target_list = get_current_context_memory(memory_data, project_root)
    target_list.append(entry)
    save_memory_structure(memory_data)

def load_system_prompt():
    """Charge le prompt système selon le mode actif"""
    global current_mode
    mode_file = Path(f"prompts/modes/{current_mode}.txt")
    if mode_file.exists():
        return mode_file.read_text(encoding="utf-8")
    
    prompt_file = Path("prompts/system.txt")
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
        
    return "Tu es NEMESIS, un assistant IA expert et concis."

def ask_llm(prompt, model=None, stream=False):
    """Envoie une requête au modèle Ollama (avec option de streaming)"""
    target_model = model or MODES[current_mode]["model"]
    try:
        process = subprocess.Popen(
            ["ollama", "run", target_model],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        process.stdin.write(prompt)
        process.stdin.close()
        
        if stream:
            def generator():
                full_response = []
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        full_response.append(line)
                        yield line
                
                # Check for errors
                if process.returncode != 0 and process.returncode is not None:
                    err = process.stderr.read()
                    yield f"\n❌ Erreur Ollama ({target_model}): {err}"
            return generator()
        else:
            out, err = process.communicate()
            if process.returncode != 0:
                return f"❌ Erreur Ollama ({target_model}): {err}"
            return out.strip()
    except Exception as e:
        return f"❌ Erreur: {str(e)}"

def read_file_command(filepath):
    """Lit le contenu d'un fichier"""
    try:
        path = Path(filepath)
        if not path.exists():
            return None, f"❌ Introuvable: {filepath}"
        if path.stat().st_size > 100000:
            return None, f"❌ Trop volumineux: {filepath}"
        content = path.read_text(encoding="utf-8")
        return content, f"📄 Contenu de {filepath}:\n\n{content}"
    except Exception as e:
        return None, f"❌ Erreur lecture: {str(e)}"

def summarize_memory(memory_segment):
    """Résume une portion de l'historique"""
    print("⏳ Résumé de l'ancien historique...")
    text = "\n".join([f"{e['role']}: {e['content']}" for e in memory_segment])
    prompt = f"Résume cette conversation de manière technique et concise:\n\n{text}"
    return ask_llm(prompt, model=DEFAULT_MODEL) # Toujours utiliser le modèle rapide pour les tâches de fond

def expand_search_query(user_input, recent_context):
    """Reformule la requête pour le RAG"""
    # Optimisation : Si la requête est très courte ou simple, on skip pour sauver du temps
    simple_keywords = ["salut", "hey", "bonjour", "ça va", "merci", "quelle heure", "qui es-tu"]
    if len(user_input) < 15 or any(kw in user_input.lower() for kw in simple_keywords):
        return user_input

    if not recent_context:
        return user_input
    
    # Contexte court (2 derniers messages)
    short_context = recent_context[-2:] if len(recent_context) > 2 else recent_context
    context_str = "\n".join([f"{m['role']}: {m['content']}" for m in short_context])

    prompt = f"""
Reformule la dernière question de l'utilisateur pour qu'elle soit autonome et explicite, en te basant sur l'historique.
Retourne UNIQUEMENT la question reformulée.

HISTORIQUE:
{context_str}

QUESTION: {user_input}
"""
    print("🔍 Optimisation de la recherche...")
    return ask_llm(prompt, model=DEFAULT_MODEL)

def process_command(user_input, memory_data, project_root):
    """Traite les commandes /"""
    global current_mode, rag_memory
    
    if user_input.startswith("/mode"):
        parts = user_input.split()
        if len(parts) == 1:
            res = "\n🎭 MODES:\n"
            for k, v in MODES.items():
                ind = "🔥" if k == current_mode else "  "
                res += f"{ind} {k:10} [{v['model']}] - {v['desc']}\n"
            return res
        
        new_mode = parts[1].lower()
        if new_mode in MODES:
            current_mode = new_mode
            return f"✅ Mode activé: {new_mode} ({MODES[new_mode]['model']})"
        return "❌ Mode inconnu."

    if user_input.startswith("/read "):
        fpath = user_input[6:].strip()
        raw, fmt = read_file_command(fpath)
        print(f"\n{fmt}\n")
        if raw and rag_memory:
            print(f"🧠 Indexation de {fpath}...")
            rag_memory.add_text(raw, source=fpath, type="file_content")
        
        return ask_llm(f"Analyse ce fichier:\n\n{fmt}")

    if user_input.startswith("/memorize "):
        if rag_memory:
            rag_memory.add_text(user_input[10:].strip(), source="user_note", type="note")
            return "✅ Note mémorisée."
        return "❌ RAG inactif."

    if user_input == "/clear":
        memory_data["projects"][project_root] = []
        save_memory_structure(memory_data)
        return "🧹 Mémoire effacée."

    if user_input == "/help":
        return "Commandes: /mode, /read, /memorize, /clear, /help, exit"

    return None

def main():
    global current_mode, rag_memory
    
    # Init
    memory = load_memory_structure()
    root = get_project_root()
    pname = Path(root).name if root != "global" else "GLOBAL"
    
    rag_dir = Path(root) / ".nemesis_rag" if root != "global" else Path.home() / ".nemesis_global_rag"
    rag_memory = RAGMemory(storage_dir=rag_dir)

    print(f"\n🧠 NEMESIS ({pname}) | RAG: ON")
    print(f"Modèle actuel: {MODES[current_mode]['model']}")
    print("---------------------------------------------------")

    while True:
        try:
            prompt_users = f"🔥 {current_mode.upper()} >> "
            u_input = input(prompt_users).strip()
            if not u_input: continue
            if u_input.lower() in ["exit", "q"]: break

            # Commandes
            res = process_command(u_input, memory, root)
            if res:
                if u_input.startswith("/read"):
                    add_memory_entry(memory, root, "user", u_input)
                    add_memory_entry(memory, root, "nemesis", res)
                print(f"\n{res}\n")
                continue

            # Gestion Mémoire (Auto-Summary)
            curr_mem = get_current_context_memory(memory, root)
            if sum(len(m['content']) for m in curr_mem) > MAX_MEMORY_CHARS * SUMMARY_THRESHOLD and len(curr_mem) > 4:
                idx = len(curr_mem) // 2
                summary = summarize_memory(curr_mem[:idx])
                
                if rag_memory:
                    rag_memory.add_text(summary, source="auto_summary", type="summary")
                
                sys_entry = {"role": "system", "content": f"RÉSUMÉ:\n{summary}", "timestamp": get_timestamp()}
                memory["projects"][root] = [sys_entry] + curr_mem[idx:]
                save_memory_structure(memory)
                curr_mem = get_current_context_memory(memory, root)

            # RAG + Expansion
            rag_context = ""
            if rag_memory:
                q = expand_search_query(u_input, curr_mem)
                hits = rag_memory.search(q, k=RAG_RESULT_COUNT)
                if hits:
                    rag_context = "\nSOURCE RAG:\n" + "\n".join([f"- {h['content'][:200]}..." for h in hits])

            # Construction Context
            ctx_msgs = []
            cur_len = 0
            for m in reversed(curr_mem):
                s = f"{m['role']}: {m['content']}"
                if cur_len + len(s) > MAX_MEMORY_CHARS: break
                ctx_msgs.insert(0, s)
                cur_len += len(s)

            full_prompt = f"""{load_system_prompt()}

{rag_context}

CONTEXTE:
{"\n".join(ctx_msgs)}

USER: {u_input}
"""
            print("\n💭 Pensée en cours...\n")
            
            # Utilisation du streaming
            full_response = ""
            for chunk in ask_llm(full_prompt, stream=True):
                sys.stdout.write(chunk)
                sys.stdout.flush()
                full_response += chunk
            
            print("\n") # Fin de réponse
            
            add_memory_entry(memory, root, "user", u_input)
            add_memory_entry(memory, root, "nemesis", full_response.strip())

        except KeyboardInterrupt:
            print("\n👋 Sortie...")
            break
        except Exception as e:
            print(f"❌ Crash: {e}")

if __name__ == "__main__":
    main()
