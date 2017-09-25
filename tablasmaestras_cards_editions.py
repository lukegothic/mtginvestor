ediciones CK --> MASTER

UPDATE editions
SET code_ck = ck.id
FROM ck_editions ck
WHERE lower(ck.name) = lower(editions.name)

RELLENAR A MANO EL RESTO
    
