import os

def create_directory_structure():
    base_dir = r"c:\finished project\AATES"
    
    directories = [
        r"apps\api",
        r"apps\worker",
        r"assets\registry",
        r"brain\ceo",
        r"brain\director",
        r"brain\planner",
        r"brain\reasoning",
        r"brain\budget",
        r"brain\story_bible",
        r"brain\timeline",
        r"brain\story",
        r"brain\decision",
        r"brain\critics\story",
        r"brain\critics\dialogue",
        r"brain\critics\continuity",
        r"brain\critics\visual",
        r"brain\critics\quality",
        r"brain\memory\short_term",
        r"brain\memory\long_term",
        r"brain\memory\semantic",
        r"brain\memory\episodes",
        r"brain\memory\characters",
        r"brain\memory\universes",
        r"contracts\events",
        r"contracts\interfaces",
        r"contracts\dto",
        r"contracts\schemas",
        r"contracts\responses",
        r"contracts\requests",
        r"core\config",
        r"core\auth",
        r"core\database",
        r"core\logging",
        r"core\workflow\engine",
        r"core\workflow\executions",
        r"core\workflow\definitions",
        r"core\workflow\checkpoints",
        r"domains\users",
        r"domains\stories",
        r"domains\universes",
        r"domains\episodes",
        r"domains\characters",
        r"domains\production",
        r"domains\publishing",
        r"domains\analytics",
        r"deployment\docker",
        r"deployment\terraform",
        r"docs\adr",
        r"knowledge\genres",
        r"knowledge\styles",
        r"knowledge\camera",
        r"knowledge\lighting",
        r"knowledge\cinematography",
        r"knowledge\dialogues",
        r"knowledge\music",
        r"knowledge\templates",
        r"metrics\system",
        r"metrics\ai",
        r"metrics\production",
        r"metrics\business",
        r"prompts\director",
        r"prompts\writer",
        r"prompts\dialogue",
        r"prompts\story",
        r"prompts\review",
        r"prompts\publisher",
        r"production\queue",
        r"providers\llm",
        r"providers\image",
        r"providers\video",
        r"providers\voice",
        r"providers\music",
        r"providers\storage",
        r"providers\scheduler",
        r"providers\eventbus",
        r"providers\rendering",
        r"rendering\queue",
        r"rendering\workers",
        r"rendering\encoding",
        r"rendering\optimization",
        r"rendering\delivery",
        r"runtime\orchestrator",
        r"runtime\registry",
        r"runtime\execution",
        r"runtime\state",
        r"runtime\context",
        r"runtime\dependency",
        r"runtime\plugins",
        r"runtime\telemetry",
        r"runtime\lifecycle",
        r"sdk",
        r"shared",
        r"tests"
    ]
    
    print("Initializing AATES Directory Structure...")
    for directory in directories:
        path = os.path.join(base_dir, directory)
        os.makedirs(path, exist_ok=True)
        # Create a .gitkeep file to ensure directory persists in version control
        gitkeep = os.path.join(path, ".gitkeep")
        with open(gitkeep, "w") as f:
            pass
        print(f"Created: {directory}")
    print("Workspace directories initialization complete.")

if __name__ == "__main__":
    create_directory_structure()
