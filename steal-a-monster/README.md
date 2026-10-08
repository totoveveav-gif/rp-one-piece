# 🦖 STEAL A MONSTER (jeu Roblox)

> Des joueurs ont des monstres qui rapportent de l'argent… et peuvent se les voler.

Ce dossier contient **tout le code Luau** du jeu, organisé pour Roblox Studio.
Le reste du dépôt (`blender/`, map GMod…) n'a rien à voir avec ce jeu.

---

## ✅ État d'avancement

| Phase | Contenu | État |
|---|---|---|
| 1 | Architecture + map + bases | ✅ **terminée** |
| 2 | Monstres + collection (Monster Road, 40+ monstres, Index) | ⏳ prochaine |
| 3 | Économie (coins, revenu/sec, collecte) | ⏳ |
| 4 | Vol + défense (LOCK, SHIELD, TRAP, ALARM) | ⏳ |
| 5 | Progression + upgrades de base | ⏳ |
| 6 | Rebirth | ⏳ |
| 7 | Événements live | ⏳ |
| 8 | UI premium | ⏳ |
| 9 | DataStore (sauvegarde) | ⏳ |
| 10 | Monétisation | ⏳ |
| 11 | Quêtes + daily/weekly | ⏳ |
| 12 | Optimisation | ⏳ |
| 13 | Polish final | ⏳ |

---

## 🚀 Installation (choisis UNE méthode)

### Méthode 1 — La plus simple (recommandée) : ouvrir le fichier tout prêt

1. Télécharge **`StealAMonster.rbxlx`** (dans ce dossier) sur ton PC.
   Sur GitHub : clique sur le fichier → bouton **Download raw file** (icône ⬇️).
2. Double-clique dessus : il s'ouvre dans **Roblox Studio** avec tous les scripts déjà rangés.
   *(En mode édition la place paraît vide, c'est normal : la map est construite par script quand tu cliques sur ▶ Play.)*
3. **File → Publish to Roblox** (crée ton jeu sur ton compte).
4. Fais la configuration ci-dessous (⚙️), puis clique sur **▶ Play**.

### Méthode 2 — Copier-coller à la main dans Studio

Dans une place **vide** (template *Baseplate*), crée exactement cette arborescence.
Clic droit sur le parent → **Insert Object** → choisis le type indiqué → renomme-le.
Ouvre chaque script et colle le contenu du fichier correspondant.

| 📍 EMPLACEMENT dans Studio | 📄 NOM | Type | Fichier à copier |
|---|---|---|---|
| ReplicatedStorage | `Shared` | Folder | — |
| ReplicatedStorage › Shared | `Net` | ModuleScript | `src/shared/Net.luau` |
| ReplicatedStorage › Shared | `Config` | Folder | — |
| ReplicatedStorage › Shared › Config | `GameConfig` | ModuleScript | `src/shared/Config/GameConfig.luau` |
| ReplicatedStorage › Shared › Config | `BaseConfig` | ModuleScript | `src/shared/Config/BaseConfig.luau` |
| ServerScriptService | `Server` | Folder | — |
| ServerScriptService › Server | `Main` | **Script** | `src/server/Main.server.luau` |
| ServerScriptService › Server | `Services` | Folder | — |
| ServerScriptService › Server › Services | `MapService` | ModuleScript | `src/server/Services/MapService.luau` |
| ServerScriptService › Server › Services | `BaseService` | ModuleScript | `src/server/Services/BaseService.luau` |
| ServerScriptService › Server | `Builders` | Folder | — |
| ServerScriptService › Server › Builders | `BaseBuilder` | ModuleScript | `src/server/Builders/BaseBuilder.luau` |
| ServerScriptService › Server | `Util` | Folder | — |
| ServerScriptService › Server › Util | `PartFactory` | ModuleScript | `src/server/Util/PartFactory.luau` |
| StarterPlayer › StarterPlayerScripts | `Client` | Folder | — |
| StarterPlayer › StarterPlayerScripts › Client | `Main` | **LocalScript** | `src/client/Main.client.luau` |
| StarterPlayer › StarterPlayerScripts › Client | `Controllers` | Folder | — |
| … › Client › Controllers | `NotificationController` | ModuleScript | `src/client/Controllers/NotificationController.luau` |
| … › Client › Controllers | `BaseMarkerController` | ModuleScript | `src/client/Controllers/BaseMarkerController.luau` |

⚠️ Les noms doivent être **exactement** identiques (majuscules comprises).
Inutile de supprimer le Baseplate : le script le retire tout seul au lancement.
Quand tout est collé : **File → Publish to Roblox** (nécessaire pour régler Max Players).

### Méthode 3 — Rojo (pour plus tard, quand tu seras à l'aise)

```bash
rojo serve default.project.json    # synchronisation en direct avec le plugin Rojo de Studio
rojo build default.project.json -o StealAMonster.rbxlx   # régénère le fichier de la méthode 1
```

---

## ⚙️ Configuration (une seule fois)

| Où | Réglage | Valeur | Pourquoi |
|---|---|---|---|
| Home → **Game Settings** → Places → (ta place) → Max Players *(seulement après **File → Publish to Roblox** ; inutile pour tester dans Studio)* | Max Players | **8** | 1 joueur = 1 base, il y a 8 bases |
| Explorer → **Workspace** → Properties | `StreamingEnabled` | **décoché** (false) | Petite map : tout le monde voit toutes les bases en permanence (déjà fait dans le `.rbxlx`) |

Rien d'autre : la map, l'éclairage, les bases et les remotes sont **générés par script**.

---

## 🧪 Tester la Phase 1

1. Clique sur **▶ Play**. Dans la fenêtre **Output** (View → Output) tu dois voir :
   `[Steal a Monster] Serveur prêt ✅` — et **aucune ligne rouge**.
2. **Secondes 0-5** : tu apparais **directement dans ta base**, la caméra tournée vers tes emplacements de monstres.
3. Une grande bannière animée s'affiche : **🏠 THIS IS YOUR BASE!**
4. Au-dessus de l'entrée : ton **nom**, ton **avatar** et `LVL 1 • STARTER CAMP`.
5. Sors de ta base : un marqueur **🏠 YOUR BASE ▼** apparaît au-dessus (visible à travers les murs) et disparaît quand tu rentres.
6. Explore : la **Monster Road** violette au centre, le **portail** au sud, l'**Event Zone** au nord, les 8 bases (4 de chaque côté).
7. Teste les 7 niveaux de base en tapant dans le chat (fonctionne **uniquement dans Studio**) :
   - `!lvl 1` … `!lvl 7` → la base se reconstruit instantanément (murs, décor, emplacements débloqués)
   - `!home` → te renvoie dans ta base
8. Test multijoueur : onglet **Test** → **Clients and Servers** → 3 joueurs → **Start**.
   Chaque joueur a sa propre base, sa couleur et son nom sur le panneau.
   Ferme un client : sa base redevient **EMPTY BASE**.

| Niveau | Nom | Emplacements | Ce qui change visuellement |
|---|---|---|---|
| 1 | Starter Camp | 6 | Palissade en bois **basse (sautable !)**, torches |
| 2 | Stone Outpost | 8 | Murs en pierre **trop hauts pour être sautés** (entrée obligatoire), piliers d'angle |
| 3 | Iron Fortress | 12 | Murs en brique, lampadaires, corniches métal |
| 4 | Royal Keep | 16 | Marbre, grès, bannières à ta couleur, dorures |
| 5 | Crystal Citadel | 20 | Murs de glace, cristaux néon scintillants sur les piliers |
| 6 | Monster Palace | 24 | Palais de marbre et d'or + **statue géante** visible de toute la map |
| 7 | Cosmic Throne | 30 | Murs en champ de force, anneau cosmique flottant, particules |

---

## 🏗️ Architecture

```
ReplicatedStorage
└── Shared                      (lisible par le client : aucune donnée sensible)
    ├── Net                     crée / récupère tous les RemoteEvents
    └── Config
        ├── GameConfig          réglages globaux (taille map, couleurs, police…)
        └── BaseConfig          les 7 niveaux de base (slots, coût, visuel)
ServerScriptService
└── Server
    ├── Main                    démarre les services : Init() puis Start()
    ├── Services
    │   ├── MapService          génère map, route, portail, arène, éclairage
    │   └── BaseService         attribue les bases, spawn dans la base, API pour les phases suivantes
    ├── Builders
    │   └── BaseBuilder         géométrie des bases + décor des 7 niveaux
    └── Util
        └── PartFactory         helpers de construction (Parts, textes, lumières, particules)
StarterPlayer › StarterPlayerScripts
└── Client
    ├── Main                    démarre les contrôleurs
    └── Controllers
        ├── NotificationController   toasts + bannières animées (mobile-first)
        └── BaseMarkerController     marqueur "🏠 YOUR BASE" + caméra tournée vers tes monstres au spawn
Workspace (généré au lancement)
├── Map           sol, trottoirs, arbres, lampadaires, limites
├── MonsterArea   Monster Road, portail, marqueurs RoadStart / RoadEnd
├── EventArea     arène des événements, marqueur ArenaCenter
└── Bases         Base_1 … Base_8
```

**Règles d'architecture (valables pour toutes les phases) :**
- Le serveur décide de **tout** (argent, monstres, vols, bases). Le client ne fait qu'afficher et demander.
- Un seul `Script` serveur et un seul `LocalScript` client ; tout le reste est en `ModuleScript`.
- Ajouter un service = créer le module + ajouter son nom dans `SERVICE_ORDER` de `Main`.
- Aucune boucle à chaque frame : les vérifications tournent toutes les 0,5 s au maximum.

---

## 🎮 Choix de game design de la Phase 1 (et pourquoi)

1. **Monster Road au centre** : en Phase 2, les monstres sortiront du portail et **défileront** sur la route.
   On les achète en marchant jusqu'à eux, au lieu d'un menu de boutique.
   → Compréhensible en 5 secondes sur un TikTok, et deux joueurs peuvent se disputer le même monstre rare.
2. **Toutes les bases face à la route** : chacun voit la base des autres → les cibles sont évidentes et les riches sont visibles.
3. **Murs du niveau 1 sautables (4 studs)** : une base débutante est facile à piller, mais elle ne contient que des monstres communs.
   Dès le niveau 2, les murs ne sont plus sautables (même depuis un socle) → il faut passer par **l'entrée**, que le LOCK BASE (Phase 4) pourra fermer.
   Les décors (torches, lampadaires, statue) ne sont pas solides : impossible de s'en servir comme échelle.
4. **Emplacements remplis du fond vers l'entrée** : les premiers monstres sont les plus loin de la route, donc le voleur met plus de temps à repartir et le propriétaire a le temps de réagir.
5. **Event Zone au bout de la route** : les événements KING MONSTER / BOSS auront lieu loin des bases.
   Y aller = laisser sa base sans surveillance → vrai dilemme risque/récompense.
6. **Amis placés côte à côte** automatiquement : jouer avec ses amis est naturel (entraide ou rivalité de voisins).
7. **Statue géante au niveau 6** : un joueur riche est repérable de loin. Statut social + cible désirable.

### ⚠️ Une idée du cahier des charges que je modifie

**« Secondes 45-60 : SOMEONE IS STEALING! »** — Sur un serveur vide, ou face à un joueur expérimenté, ça ne peut pas être garanti.
Et se faire voler par un vrai joueur dans sa première minute fait **quitter le jeu**.
➡️ **Solution (Phase 4)** : un PNJ « voleur gobelin » tente de voler le 2ᵉ monstre du nouveau joueur vers la 50ᵉ seconde.
Il est facile à arrêter (on le touche) → le joueur découvre le vol **et** la défense, il ressent l'émotion et finit sur une victoire.
En parallèle, un **bouclier débutant** de quelques minutes empêche les vrais joueurs de le voler tout de suite.

**Gems** : elles seront aussi gagnables en jouant (quêtes, paliers de collection), pas seulement avec des Robux.
Sinon le jeu paraît « pay-to-win » et les joueurs gratuits partent.
