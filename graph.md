[mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	init(init)
	guess(guess)
	evaluate(evaluate)
	__end__([<p>__end__</p>]):::last
	__start__ --> init;
	evaluate -. &nbsp;end&nbsp; .-> __end__;
	evaluate -. &nbsp;continue&nbsp; .-> guess;
	guess --> evaluate;
	init --> guess;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

](http://_vscodecontentref_/1)
