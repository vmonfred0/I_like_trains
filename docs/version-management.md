# Version Management and Updates

## Checking Your Version

To ensure you have the latest version of the project:

1. **For Git users**:
   ```bash
   # Check your current commit hash
   git rev-parse HEAD
   
   # Check for updates without applying them
   git fetch origin
   git log HEAD..origin/main --oneline
   ```
   If the second command shows any commits, your local version is behind the remote repository.

2. **For archive users** (zip/tar.gz):
   - Check the download date of your archive
   - Visit https://github.com/vita-epfl/I_like_trains/releases to see if a newer version is available

## Updating Your Project

1. **For Git users**:
   ```bash
   # First, backup your work (especially your agent files and config.json)
   cp -r common/agents/your_agent.py common/agents/your_agent_backup.py
   cp config.json config.json.backup
   
   # Then pull the latest changes
   git pull origin main --rebase
   ```

2. **For archive users**:
   - Download the latest archive
   - Extract it to a new directory
   - Copy your agent files and configuration from the old directory to the new one

## Handling Conflicts

When updating, you might encounter conflicts, especially if you've modified files that were also updated in the repository.

1. **For file conflicts**:
   - You should generally not modify the core game files outside the designated areas
   - If you encounter conflicts in these files, you may need assistance from a TA (or a LLM)
   - In Git, you can see which files have conflicts with `git status`

## Backing Up Your Work

Regular backups are essential to prevent data loss:

- **Manual backups**: Regularly copy your important files (especially your agent implementations) to a separate location
- **Version control**: If using Git, commit your changes frequently to track your progress
- **Automated backups**: Use your operating system's backup features (Time Machine on macOS, File History on Windows) for regular automated backups
- **Cloud storage**: Consider using cloud storage services for an additional layer of protection

**Important**: Always back up your work before updating to a new version of the project.
