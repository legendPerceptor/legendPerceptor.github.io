---
title: 如何在Ubuntu 22.04中使用中文输入法
author: yuanjian
date: 2024-03-06 09:34:00 -0500
categories: [Tutorial]
tags: [input method, Chinese input]
pin: true
---

如果你很早之前就开始使用Ubuntu系统，你可能安装了搜狗输入法，因为以前系统自带的输入法总是有各种各样奇怪的问题，而且安装起来特别麻烦，装好了还莫名奇妙不能用。这篇文章就带你彻底搞定在Ubuntu系统下输入法的问题。

我们主要讨论Ubuntu 22.04以及更新版本的解决方案。首先你会发现搜狗输入法不更新了，最新版本只到Ubuntu 20.04。不过幸运的是，Ubuntu自带的输入法已经做得挺好了，我们只需要在设置中找到并正确安装就行了。

## 正确安装后

首先我们来看下装好以后是怎么样的。从屏幕右上角，右键打开设置，找到Keyboard/键盘，在Input Sources里面应该有一个 Chinese (Intelligent Pinyin)的选项。这样在你按下 `Windows键 + 空格` 的时候，应该会在`en`和`拼`之间切换。

> 注意这里的中文应该会显示`拼`而不是`zh`或者其他的，否则还是打不出中文。
{: .prompt-tip }

![Ubuntu Input Method After Installation](https://i.ibb.co/Kqs0w0j/2024-03-06-12-12-Ubuntu-Input.png)

## 如何安装

你的系统一开始可能只支持英语，需要在设置中找到 `Region&Language` 然后点 `Manage Installed Languages`。如果你的语言历表中没有`汉语（中国）`的字样，点击 `Install/Remove Languages`，找到 `Chinese (simplified)`，选中以后点击 `Apply`，系统就会开始安装语言。

系统语言安装好以后，可以选择把菜单和窗口的语言也设置成中文。只需要把`汉语（中国）`拖动到第一个就行了。

![set Chinese for menus and windows](https://i.ibb.co/1QJmvSD/2024-03-06-12-25-menu-chinese.png)

然后就是设置输入法了，在设置的`Keyboard`中，点击 `Add an Input Source`，如果里面还没有Chinese，就点下面的3个点把Chinese加上。

> 重点来了，很多朋友会发现Chinese已经在里面了，但就是输入不了中文
{: .prompt-warning }

因为Chinese这个输入源里面还有很多种方式可以选，需要点击`Chinese`这个按钮（没错它可以点），在弹出的新列表里选择`Chinese (Intelligent Pinyin)`。

![select Chinese (Intelligent Pinyin)](https://i.ibb.co/PCJd6Rb/2024-03-06-12-34-Select-Chinese.png)

最后这个步骤很关键，比较隐蔽，因为你可能不知道这个Chinese还是可以点的按钮，然后花了好长时间在网上搜为什么打不出中文。再强调一下，最后你切换到中文的时候应该是显示`拼`而不是`zh`。

## VS Code的中文输入问题

你可能会发现，输入法设置好了，在Chrome浏览器里都可以正常输入中文了，但在VS Code里面就是输入不了。这很有可能是因为你使用了snap安装VS Code。建议直接卸载然后去官网下载一个`.deb`安装包。

```bash
which code
# 如果是/snap/bin 之类的输出
sudo snap remove code
```

下载好以后就可以使用类似与下面的命令安装VS Code

```bash
sudo dpkg -i ./code_1.87.0-1709078641_amd64.deb
```

这样你就可以在VS Code中输入中文啦！不过VS Code在Ubuntu上对中文的支持有时候还是会有一些bug，有的时候会突然就删除不了字符或者输入不了字符，如果发生这种情况就重启一下 VS Code。希望微软或者其他开源开发者能早日修复类似的Bug吧！