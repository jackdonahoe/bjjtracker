-- Fake data for the public demo deployment. Never run against production.
-- Intervals are relative to now() so the demo stays "fresh" indefinitely
-- without needing to be reseeded.

insert into sessions (held_at) values
    (now() - interval '9 weeks'),
    (now() - interval '8 weeks'),
    (now() - interval '7 weeks'),
    (now() - interval '6 weeks'),
    (now() - interval '5 weeks'),
    (now() - interval '4 weeks'),
    (now() - interval '3 weeks'),
    (now() - interval '2 weeks'),
    (now() - interval '1 week'),
    (now() - interval '2 days');

insert into people (full_name, email, source, first_seen) values
    -- core regulars: check in almost every week (4+ bucket)
    ('Maya Chen', 'maya.chen@example.com', 'friend', now() - interval '9 weeks'),
    ('Ethan Brooks', 'ethan.brooks@example.com', 'tabling', now() - interval '9 weeks'),
    ('Priya Patel', 'priya.patel@example.com', 'social_media', now() - interval '8 weeks'),
    ('Jordan Vance', 'jordan.vance@example.com', 'class_announcement', now() - interval '8 weeks'),
    -- came a handful of times (3 bucket)
    ('Lena Ortiz', 'lena.ortiz@example.com', 'friend', now() - interval '4 weeks'),
    ('Marcus Webb', 'marcus.webb@example.com', 'social_media', now() - interval '4 weeks'),
    ('Tasha Reid', 'tasha.reid@example.com', 'tabling', now() - interval '3 weeks'),
    -- came twice (2 bucket)
    ('Owen Blake', 'owen.blake@example.com', 'friend', now() - interval '2 weeks'),
    ('Sofia Marsh', 'sofia.marsh@example.com', 'other', now() - interval '2 weeks'),
    ('Derek Nolan', 'derek.nolan@example.com', 'class_announcement', now() - interval '2 weeks'),
    -- came once, recently (1 bucket, not gone quiet)
    ('Grace Kim', 'grace.kim@example.com', 'social_media', now() - interval '1 week'),
    ('Wyatt Foster', 'wyatt.foster@example.com', 'friend', now() - interval '1 week'),
    ('Nina Alvarez', 'nina.alvarez@example.com', 'tabling', now() - interval '3 days'),
    -- came once, a long time ago (1 bucket, gone quiet)
    ('Colin Pierce', 'colin.pierce@example.com', 'other', now() - interval '9 weeks'),
    ('Ravi Sundaram', 'ravi.sundaram@example.com', 'friend', now() - interval '9 weeks'),
    ('Bianca Torres', 'bianca.torres@example.com', 'class_announcement', now() - interval '8 weeks');

insert into check_ins (person_id, session_id, checked_in)
select v.person_id, v.session_id, s.held_at
from (values
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10),
    (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10),
    (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10),
    (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10),
    (5, 6), (5, 8), (5, 9),
    (6, 7), (6, 8), (6, 10),
    (7, 8), (7, 9), (7, 10),
    (8, 9), (8, 10),
    (9, 8), (9, 10),
    (10, 9), (10, 10),
    (11, 10),
    (12, 9),
    (13, 10),
    (14, 1),
    (15, 1),
    (16, 2)
) as v(person_id, session_id)
join sessions s on s.id = v.session_id;

-- password is "demo1234"
insert into admins (email, password_hash) values
    ('demo@example.com', '$2b$12$y4v5B185boy0IOXkzpguTu.QVT2wn8O7phXqD2J3bxZYGTsst3Gma');
