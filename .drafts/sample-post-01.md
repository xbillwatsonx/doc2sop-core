Tonight doc2sop got its first taste of production chaos.

Spent three hours wrestling with Python imports after merging the repo setup. Local worked fine. Server didn't. Classic.

Turns out I had absolute imports in the package but relative imports are what actually work when you deploy. Third PR fixed it. Server's live at 207.246.117.224:8080 now.

Testing this on our own workflow first. When you're converting messy shop notes into actual SOPs, the last thing you need is the tool itself being messy.

GitHub: xbillwatsonx/doc2sop-core

#doc2sop #buildinpublic