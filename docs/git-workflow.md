# Tracking Your Changes with Git

If you want to track your changes with Git while still being able to receive updates from the original repository, follow these steps:

## 1. Fork the Repository

1. Go to the original repository at https://github.com/vita-epfl/I_like_trains
2. Click the "Fork" button in the top-right corner of the page
3. This creates a copy of the repository under your GitHub account

## 2. Clone Your Fork

Clone your forked repository to your local machine:

```bash
git clone https://github.com/YOUR_USERNAME/I_like_trains.git
cd I_like_trains
```

Replace `YOUR_USERNAME` with your GitHub username.

## 3. Set Up the Upstream Remote

To keep your fork up to date with the original repository, add it as an "upstream" remote:

```bash
git remote add upstream https://github.com/vita-epfl/I_like_trains.git
```

Verify your remotes are set up correctly:

```bash
git remote -v
```

You should see both `origin` (your fork) and `upstream` (the original repository).

## 4. Keeping Your Fork Updated

To update your fork with changes from the original repository:

```bash
# Fetch changes from the upstream repository
git fetch upstream

# Make sure you're on your main branch
git checkout main

# Merge changes from upstream/main into your local main branch
git merge upstream/main

# Push the changes to your fork on GitHub
git push origin main
```

## 5. Using GitHub's UI to Update Your Fork

You can also update your fork using GitHub's web interface:

1. Navigate to your fork on GitHub
2. Click on "Sync fork" button (located above the file list)
3. Click "Update branch" to update your fork with the latest changes from the original repository

## 6. Working on Your Changes

Create a branch for your changes to keep your work organized:

```bash
git checkout -b my-agent-implementation
```

Make your changes, then commit and push them:

```bash
git add .
git commit -m "Implemented my agent strategy"
git push origin my-agent-implementation
```

This workflow allows you to keep your changes separate while still being able to receive updates from the original repository.
