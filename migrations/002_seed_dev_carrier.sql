-- ============================================================
-- FREITIR — Dev carrier seed
-- Gives us a known carrier_id to use before auth is wired up.
-- Run in: Supabase Dashboard → SQL Editor
-- ============================================================

insert into carriers (id, name)
values ('11111111-1111-1111-1111-111111111111', 'Dev Carrier')
on conflict (id) do nothing;
