ediciones CK --> MASTER

UPDATE editions
SET code_ck = ck.id
FROM ck_editions ck
WHERE lower(ck.name) = lower(editions.name)

RELLENAR A MANO EL RESTO

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

cards CK --> MASTER

select *
from ck_cards ckc
inner join ck_editions cke on ckc.edition = cke.id
inner join editions e on cke.id = e.code_ck
left join cards c on ckc.name = c.name and e.code = c.edition
where e.name = 'Zendikar'

-- ESTO NO VA, pero es un camino a seguir
UPDATE cards
SET ck_id = ckcards.id
FROM editions e, (SELECT ckc.id, ckc.name, cke.id as ckedition FROM ck_cards ckc
INNER JOIN ck_editions cke on ckc.edition = cke.id) as ckcards
WHERE edition = e.code and e.code_ck = ckcards.ckedition and lower(ckcards.name) = lower(cards.name)
