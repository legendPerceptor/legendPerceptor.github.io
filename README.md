# Yuanjian's Personal Website

This project contains the static files and code for generating my personal website [yuanjianliu.net](https://www.yuanjianliu.net). The page design is based on [Jekyll Chirpy Theme](https://github.com/cotes2020/jekyll-theme-chirpy).

## Get Started

The website is built on top of jekyll, so please follow [jekyll's official website](https://jekyllrb.com/) to see how to install the tools and how it works.

To make things simple, you can run the following two lines of commands to serve the website in [https://localhost:4000](https://localhost:4000).

```bash
bundle install
bundle exec jekyll s
```

## Trouble shooting

> If you see a lot of errors, you probably have not installed Ruby and other jekyll's dependencies.

Try the following commands to install dependencies on Ubuntu. For other systems you also need to install ruby properly.

```bash
sudo apt update
sudo apt install -y ruby-full ruby-dev build-essential zlib1g-dev
bundle config set --local path vendor/bundle
```
