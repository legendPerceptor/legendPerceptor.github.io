---
title: How to install Jekyll on Ubuntu and macOS
author: yuanjian
date: 2024-03-03 09:34:00 -0500
categories: [Tutorial]
tags: [Jekyll, Github Pages]
pin: true
---


## 1. Ubuntu Installation

It is good to follow the [Jekyll official document](https://jekyllrb.com/docs/installation/ubuntu/).

The first step is to install necessary dependencies.

```bash
sudo apt install ruby-full build-essential zlib1g-dev
```

As Jekyll is mainly used for Github Pages, many open-source static site generator requires `Node.js` and `npm`. It is not necessary and Jekyll's official document didn't mention it, but I had trouble with these dependencies so I will include them here. I recommend not using the `apt` to install `Node.js` because the version is too old in Ubuntu's repo. Go to [Node.js webste](https://nodejs.org/en), and click the download button. You will get a `.tar.xz` file. You can use the following command to extract the files.


> Your filename is likely to be different because of newer Nodejs versions.
{: .prompt-tip }

```bash
tar -xvf node-v20.11.1-linux-x64.tar.xz
```

I prefer to move the third-party package to /opt/ so that I can find them later. You can put them in any folder you like. We need to set PATH for the system to know where to find `node` and `npm`.

```bash
sudo mv node-v20.11.1-linux-x64/ /opt/
```



If you directly run `bundle`, Gem will try to install into your system folder, which is not recommended. If you are using the bash shell, you can execute the following commands to set a directory for Gem to install its packages.

```bash
echo '# Install Ruby Gems to ~/gems' >> ~/.bashrc
echo 'export GEM_HOME="$HOME/gems"' >> ~/.bashrc
echo 'export PATH="$HOME/gems/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Finally, you can install Jekyll and Bundler using gem.

```bash
gem install jekyll bundler
```


## 2. macOS Installation

Of course, you should visit the official documentation of [Jekyll on macOS](https://jekyllrb.com/docs/installation/macos/).

If you haven't installed `Homebrew`, you should probably install it first, not just for Jekyll, but for macOS development in general. You need a package management tool.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then we need to install `ruby` and `chruby`.

### 2.1 bash shell or zsh shell

> If you are using the default `zsh` or `bash` shell on macOS, you can follow the commands listed below. But if you use `fish` shell as I do, wait until later and follow my commands.
{: .prompt-warning }

```bash
brew install chruby ruby-install xz
```

Install the latest version of Ruby, but don't make it too new so that Jekyll does not support it.

```bash
ruby-install ruby 3.1.3
```

Then we need to write the `PATH` environment variable to let the system know where `chruby` is installed. 

```bash
echo "source $(brew --prefix)/opt/chruby/share/chruby/chruby.sh" >> ~/.zshrc
echo "source $(brew --prefix)/opt/chruby/share/chruby/auto.sh" >> ~/.zshrc
echo "chruby ruby-3.1.3" >> ~/.zshrc # run 'chruby' to see actual version
```

Don't forget to set `GEM_HOME` and `PATH` environment variable.

```bash
echo '# Install Ruby Gems to ~/gems' >> ~/.zshrc
echo 'export GEM_HOME="$HOME/gems"' >> ~/.zshrc
echo 'export PATH="$HOME/gems/bin:$PATH"' >> ~/.zshrc
source ~/.bashrc
```

Then we can install jekyll and bundler with `gem`.

```bash
gem install jekyll bundler
```


### 2.2 fish shell

However, I am using `fish shell` on masOS for better command history and color highlights. So for `fish shell`, the commands should be as follows.

Install `chruby-fish` instead of `chruby`.

```bash
brew install chruby-fish ruby-install
```

Install ruby 3.1.3 and configure the environment.

> The `chruby-fish` version is written as a constant, but it may change. Check `chruby --version` and use that version to replace `1.0.0`.
{: .prompt-warning}


```bash
ruby-install ruby 3.1.3
echo "source "(brew --prefix)"/Cellar/chruby-fish/1.0.0/share/fish/vendor_functions.d/chruby.fish" >> ~/.config/fish/config.fish
echo "source "(brew --prefix)"/Cellar/chruby-fish/1.0.0/share/fish/vendor_conf.d/chruby_auto.fish" >> ~/.config/fish/config.fish
echo "chruby ruby-3.1.3" >> ~/.config/fish/config.fish
```

Source the config file and your environment is good to go.

```bash
source ~/.config/fish/config.fish
```

We also need to set the `GEM_HOME` and `PATH` environment variable but in `fish`'s way.

```bash

echo '# Install Ruby Gems to ~/gems' >> ~/.config/fish/config.fish
echo 'set -x GEM_HOME $HOME/gems' >> ~/.config/fish/config.fish
echo 'set -x PATH $HOME/gems/bin' $PATH >> ~/.config/fish/config.fish
```

In the end, use `gem` to install jekyll.

```bash
gem install jekyll bundler
```

## Run Jekyll to serve your Github Pages

Now, navigate to your Github Pages repo. If you don't yet have one, you can go to [my repo](https://github.com/legendPerceptor/legendPerceptor.github.io) and clone it to see if your jekyll works correctly.

> My website is based on [Jekyll Theme Chirpy](https://github.com/cotes2020/jekyll-theme-chirpy). It might be easier for you to go to their repo and follow their instructions.
{: .prompt-tip }

I have a git submodule called `chirpy-static-assets` that provides necessary functionalities for the website. You need to get the submodule before asking jekyll to serve it locally.

```bash
git submodule update --init --recursive
bundle install
bundle exec jekyll s
```

After above commands, you should see some similar output as follows. And then you can go to [http://127.0.0.1:4000](http://127.0.0.1:4000) to see the website.

```text
      Generating... 
                    done in 2.053 seconds.
 Auto-regeneration: enabled for '/home/yuanjian/Research/website/jekyll-theme-chirpy'
    Server address: http://127.0.0.1:4000/
  Server running... press ctrl-c to stop.
      Regenerating: 1 file(s) changed at 2024-03-03 09:33:52
```