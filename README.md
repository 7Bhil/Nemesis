# 🧠 NEMESIS - IA Locale CLI

Assistant IA **100% local**, rapide et extensible pour la ligne de commande.

## 🚀 Démarrage rapide

```bash
# Lancer NEMESIS
python nemesis.py
```

## ✨ Fonctionnalités

- 🔒 **100% Local** - Aucune donnée ne quitte ta machine
- 💬 **Conversation intelligente** - Mémoire contextuelle des échanges
- 📄 **Lecture de fichiers** - Analyse et comprend ton code
- ⚡ **Rapide** - Basé sur Ollama et Qwen2.5
- 🎯 **Extensible** - Architecture modulaire pour ajouter des fonctionnalités

## 📋 Prérequis

- Python 3.10+
- Ollama installé
- Modèle `qwen2.5:7b` téléchargé

```bash
# Installer Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Télécharger le modèle
ollama pull qwen2.5:7b
```

## 🎮 Commandes disponibles

| Commande | Description |
|----------|-------------|
| `/read <fichier>` | Lit et analyse un fichier |
| `/clear` | Efface la mémoire de conversation |
| `/help` | Affiche l'aide |
| `exit` / `quit` | Quitte NEMESIS |

## 📁 Structure du projet

```
nemesis/
├── nemesis.py        # Point d'entrée principal
├── memory.json       # Historique des conversations (généré auto)
├── prompts/
│   └── system.txt    # Personnalité de l'IA
└── tools/
    └── (futurs outils)
```

## 🔧 Configuration

### Changer le modèle

Édite `nemesis.py` et modifie la variable `MODEL`:

```python
MODEL = "deepseek-coder:6.7b"  # Pour du code
MODEL = "qwen2.5:7b"            # Polyvalent (défaut)
```

### Personnaliser la personnalité

Édite `prompts/system.txt` pour modifier le comportement de NEMESIS.

## 🎯 Exemples d'utilisation

### Conversation simple
```
🔥 >> Explique-moi les décorateurs Python
```

### Analyse de code
```
🔥 >> /read app/models/user.py
```

### Aide au debug
```
🔥 >> J'ai une erreur "AttributeError: 'NoneType' object has no attribute 'id'"
```

## 🚀 Prochaines évolutions possibles

- [ ] Modes spécialisés (`/mode dev`, `/mode study`)
- [ ] Exécution de commandes sécurisées
- [ ] Mémoire vectorielle intelligente
- [ ] Analyse de projets complets
- [ ] Agent autonome multi-actions
- [ ] Export en binaire standalone

## ⚠️ Règle d'or

**NEMESIS ne décide rien seul.**
Il suggère. Tu confirmes. Toujours.

## 📝 License

Projet personnel - Utilise comme tu veux 🔥
# Nemesis
