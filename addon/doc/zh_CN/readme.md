# 数字处理

这是一个 NVDA 插件，可以根据数字的长度来定义数字的朗读方式（数字货数值）。

例如，默认“以数字读法读出的最小位数”为 2，启用数字处理后，会把 42（四十二） 朗读为 4 2、而 338（三百三十八） 朗读为 3 3 8 等；如果把“以数字读法读出的最小位数”设置为 4，那么会像以前一样，朗读 338为“三百三十八”， 但 1337（一千三百三十七） 会朗读为 1 3 3 7。

另外，您还可以在设置面板中，为当前配置文件开启数字处理的自动启动。

灵感来自 [德里克·里默 (Derek Riemer) 的一项实验工作。][1]

兼容NVDA 2017.3及以上，在[这里][2]下载

## 快捷键

* NVDA+shift+l（按一次）：启用/禁用数字处理；
* NVDA+shift+l（连按两次）：打开一个对话框以随时更改要进行处理的最小数字位数。

注意，快捷键可在 NVDA 的“按键与手势”对话框内进行配置。

[1]: https://github.com/derekriemer/phoneOpperationHelper
[2]: https://raw.githubusercontent.com/ABuffEr/numberProcessing/master/packages/numberProcessing-1.0-20200310-dev.nvda-addon
