# AgentDealExp

Beaver:

设置 OpenAI 的 API 和安装所需库后，直接运行 `experiment.py` 即可。循环结构已写好，但目前只会执行第一轮。

基本结构已经完成，后续可根据需要进行修改。

_prompt 需要完善!!_

代码中有很多冗余部分，之后会逐步删除。

目前执行一次实验大约需要 1 分钟。

多次运行后发现这个 agent 确实很蠢。

## TODO：

检查当前轮次的前手发言是否已加入 memory。

`prompt_factory` 感觉还是没必要，不做了。

## Structure：

![alt text](image-1.png)

⑦ 在代码中未实现。
