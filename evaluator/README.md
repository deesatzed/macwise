# MacWise Evaluator

`macwise-eval` independently judges serialized MacWise outputs against evidence capsules and
predeclared safety expectations. It does not import or execute MacWise product code.

Real-Mac receipts belong only in the ignored `private/` directory. The first implementation slice
provides the standalone command surface; capsule capture and evaluation commands follow.
