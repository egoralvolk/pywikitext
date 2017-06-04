#encoding "utf8"

Toponym -> Word<gram="geo", h-reg1>+
	| 	Word<h-reg1, gnc-agr[1]> Word<gram="geo", h-reg1, gnc-agr[1]> 
	| 	Word<gram="geo", h-reg1, gnc-agr[1]> Noun Word<h-reg1, gnc-agr[1]>
	| 	Word<h-reg1, gnc-agr[1]> Noun Word<gram="geo", h-reg1, gnc-agr[1]>;
	
S -> Toponym interp (Toponym.Name);