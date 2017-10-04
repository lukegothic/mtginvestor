ediciones CK --> MASTER

UPDATE editions
SET code_ck = ck.id
FROM ck_editions ck
WHERE lower(ck.name) = lower(editions.name)

UPDATE editions
SET code_mkm = mkm.id
FROM mkm_editions mkm
WHERE lower(mkm.name) = lower(editions.name)

RESTO A MANO-->

UPDATE editions SET code_ck = 2420	WHERE code = 'BR';
UPDATE editions SET code_ck = 2425	WHERE code = 'BD';
UPDATE editions SET code_ck = 2360	WHERE code = '6E';
UPDATE editions SET code_ck = 2902	WHERE code = 'C13';
UPDATE editions SET code_ck = 2977	WHERE code = 'CN2';
UPDATE editions SET code_ck = 2470	WHERE code = 'DM';
UPDATE editions SET code_ck = 2370	WHERE code = '8E';
UPDATE editions SET code_ck = 2355	WHERE code = '5E';
UPDATE editions SET code_ck = 2350	WHERE code = '4E';
UPDATE editions SET code_ck = 2913	WHERE code = 'V14';
UPDATE editions SET code_ck = 2395	WHERE code = 'A';
UPDATE editions SET code_ck = 2430	WHERE code = 'B';
UPDATE editions SET code_ck = 2789	WHERE code = 'M10';
UPDATE editions SET code_ck = 2847	WHERE code = 'M11';
UPDATE editions SET code_ck = 2863	WHERE code = 'M12';
UPDATE editions SET code_ck = 2876	WHERE code = 'M13';
UPDATE editions SET code_ck = 2895	WHERE code = 'M14';
UPDATE editions SET code_ck = 2910	WHERE code = 'M15';
UPDATE editions SET code_ck = 2862	WHERE code = 'CMD';
UPDATE editions SET code_ck = 2908	WHERE code = 'CNS';
UPDATE editions SET code_ck = 3044	WHERE code = 'AKHM';
UPDATE editions SET code_ck = 2984	WHERE code = 'MPS';
UPDATE editions SET code_ck = 2907	WHERE code = 'MD1';
UPDATE editions SET code_ck = 2947	WHERE code = 'MM2';
UPDATE editions SET code_ck = 3032	WHERE code = 'MM3';
UPDATE editions SET code_ck = 2375	WHERE code = '9E';
UPDATE editions SET code_ck = 2875	WHERE code = 'PC2';
UPDATE editions SET code_ck = 2625	WHERE code = 'P2';
UPDATE editions SET code_ck = 2620	WHERE code = 'P3';
UPDATE editions SET code_ck = 2854	WHERE code = 'FAL';
UPDATE editions SET code_ck = 2640	WHERE code = 'RAV';
UPDATE editions SET code_ck = 2345	WHERE code = 'R';
UPDATE editions SET code_ck = 2365	WHERE code = '7E';
UPDATE editions SET code_ck = 2380	WHERE code = '10E';
UPDATE editions SET code_ck = 2700	WHERE code = 'TSB';
UPDATE editions SET code_ck = 2720	WHERE code = 'U';
UPDATE editions SET code_ck = 2960	WHERE code = 'EXP';
UPDATE editions SET code_ck = 3058	WHERE code = 'XLN';
UPDATE editions SET code_ck = 3055	WHERE code = 'C17';

UPDATE editions SET code_mkm = 'Alpha' WHERE code = 'A';
UPDATE editions SET code_mkm = 'Beta' WHERE code = 'B';
UPDATE editions SET code_mkm = 'Magic+2014' WHERE code = 'M14';
UPDATE editions SET code_mkm = 'Magic+2015' WHERE code = 'M15';
UPDATE editions SET code_mkm = 'Commander' WHERE code = 'CMD';
UPDATE editions SET code_mkm = 'Conspiracy' WHERE code = 'CNS';
UPDATE editions SET code_mkm = 'Amonkhet+Invocations' WHERE code = 'AKHM';
UPDATE editions SET code_mkm = 'Kaladesh+Inventions' WHERE code = 'MPS';
UPDATE editions SET code_mkm = 'Modern+Masters+2015' WHERE code = 'MM2';
UPDATE editions SET code_mkm = 'Modern+Masters+2017' WHERE code = 'MM3';
UPDATE editions SET code_mkm = 'Planechase+2012' WHERE code = 'PC2';
UPDATE editions SET code_mkm = 'Premium+Deck+Series%3A+Fire+%26+Lightning' 	WHERE code = 'FAL';
UPDATE editions SET code_mkm = 'Time+Spiral' WHERE code = 'TSB';
UPDATE editions SET code_mkm = 'Revised' WHERE code = 'R';
UPDATE editions SET code_mkm = 'Battle+Royale' WHERE code = 'BR';
UPDATE editions SET code_mkm = 'Beatdown' WHERE code = 'BD';
UPDATE editions SET code_mkm = 'Sixth+Edition' WHERE code = '6E';
UPDATE editions SET code_mkm = 'Commander+2013' WHERE code = 'C13';
UPDATE editions SET code_mkm = 'From+the+Vault%3A+Annihilation' WHERE code = 'V14';
UPDATE editions SET code_mkm = 'Unlimited' WHERE code = 'U';

cards CK --> MASTER

-- esto relaciona las cartas, prueba con WWK
select c.id, c.name, c.edition, ck.id, mkm.id
from cards c
left join editions e on c.edition = e.code
left join ck_cards ck on lower(c.name) = lower(ck.name) and e.code_ck = ck.edition
left join mkm_cards mkm on lower(c.name) = lower(mkm.name) and e.code_mkm = mkm.edition
where c.edition = 'WWK'
