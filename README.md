# 🎵 Melodia - Modern Music Player

Um player de música moderno desenvolvido em Python com interface gráfica customtkinter.

## 📁 Estrutura do Projeto

O projeto foi reorganizado seguindo padrões profissionais de desenvolvimento:

```
appmusica/
├── main.py                 # Ponto de entrada da aplicação
├── requirements.txt        # Dependências do projeto
├── README.md              # Documentação do projeto
├── venv/                  # Ambiente virtual Python
└── src/                   # Código fonte principal
    ├── __init__.py
    ├── music_app.py       # Classe principal da aplicação
    ├── controllers/       # Controladores (lógica de negócio)
    │   ├── __init__.py
    │   ├── base_controller.py
    │   ├── controller.py
    │   ├── navigation_controller.py
    │   ├── player_controller.py
    │   ├── feed_controller.py
    │   ├── search_controller.py
    │   ├── playlist_controller.py
    │   └── settings_controller.py
    ├── models/            # Modelos de dados
    │   ├── __init__.py
    │   └── models.py
    ├── ui/                # Componentes de interface
    │   ├── __init__.py
    │   ├── components.py
    │   └── factory.py
    ├── managers/          # Gerenciadores de serviços
    │   ├── __init__.py
    │   └── managers.py
    ├── core/              # Componentes centrais
    │   ├── __init__.py
    │   ├── events.py      # Sistema de eventos
    │   ├── app_context.py # Contexto da aplicação
    │   └── player.py      # Player de música
    └── utils/             # Utilitários (futuro)
        └── __init__.py
```

## 🏗️ Arquitetura

### Padrão MVC/MVP
O projeto segue uma arquitetura baseada em MVC (Model-View-Controller):

- **Models** (`src/models/`): Definem as estruturas de dados (Song, SearchResult, ThemeColors)
- **Views** (`src/ui/`): Componentes de interface do usuário
- **Controllers** (`src/controllers/`): Lógica de negócio e coordenação entre models e views

### Componentes Principais

#### Core (`src/core/`)
- **EventBus**: Sistema de eventos para comunicação entre componentes
- **AppContext**: Contexto global da aplicação com injeção de dependências
- **MusicPlayer**: Engine principal de reprodução de música

#### Managers (`src/managers/`)
- **DataManager**: Gerenciamento de dados persistentes
- **SettingsManager**: Configurações da aplicação
- **DownloadManager**: Downloads de música do YouTube
- **SearchManager**: Busca de músicas
- **PlaylistManager**: Gerenciamento de playlists

#### Controllers (`src/controllers/`)
- **NavigationController**: Navegação entre telas
- **PlayerController**: Controles de reprodução
- **FeedController**: Feed de músicas
- **SearchController**: Busca e download
- **PlaylistController**: Gerenciamento de playlists
- **SettingsController**: Configurações

## 🚀 Como Executar

1. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute a aplicação:**
   ```bash
   python main.py
   ```

## 📦 Dependências

- **customtkinter**: Interface gráfica moderna
- **yt-dlp**: Download de vídeos/áudio do YouTube
- **Pillow**: Processamento de imagens
- **pyglet**: Reprodução de áudio com suporte a crossfade
- **sounddevice**: Dispositivos de áudio

## 🎯 Funcionalidades

- ✅ Interface moderna e responsiva
- ✅ Download de músicas do YouTube
- ✅ Reprodução de áudio com controles completos
- ✅ Sistema de playlists
- ✅ Busca e organização de músicas
- ✅ Configurações personalizáveis
- ✅ croosfade(semelhante ao do spotify)
- ✅ Temas claro/escuro
- ✅ Sistema de eventos desacoplado

## 📝 Notas de Desenvolvimento

- Todos os imports foram atualizados para usar imports relativos
- Sistema de injeção de dependências via AppContext
- Padrão Observer implementado via EventBus
- Componentes UI reutilizáveis e modulares
- Gerenciamento de estado centralizado

baixe o projeto compilado em https://github.com/devlohranbala/melodia/releases 
---

**Desenvolvido com ❤️ em Python**