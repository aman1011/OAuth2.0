#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import Base, Music_Band, Album, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# connect to database
engine = create_engine('sqlite:///musicbandswithalbums.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

Music_Bands = session.query(Music_Band).all()
for band in Music_Bands:
	print band.id
	print band.name
	print band.user_id

# Insert Bands
session.add(Music_Band(name='Linkin Park', user_id=1,))
session.commit()

session.add(Music_Band(name='Porcupine Tree', user_id=1,))
session.commit()

session.add(Music_Band(name='Breaking Benajamin', user_id=1,))
session.commit()

session.add(Music_Band(name='Alcest', user_id=1,))
session.commit()

session.add(Music_Band(name='Autumn for the crippled child', user_id=1,))
session.commit()

session.add(Music_Band(name='Steven Wilson', user_id=1,))
session.commit()

session.add(Music_Band(name='Bring me the Horizon', user_id=1,))
session.commit()

session.add(Music_Band(name='Les Discrets', user_id=1,))
session.commit()


# Adding albums for the bands

session.add(Album(name='Hybrid Theory', description="Hybrid Theory is the debut studio album by American rock band Linkin Park, released on October 24, 2000 through Warner Bros. Records. As of 2017, the album has been certified diamond by the RIAA for sales in the band's home country of United States, with over eleven million units, peaking at number two on the US Billboard 200 and it also has reached high positions on other charts worldwide, with 30 million copies sold, making it the best-selling debut album since Guns N' Roses' Appetite for Destruction and the best-selling rock album of the 21st century.", music_band_id=1, user_id=1))
session.commit()

session.add(Album(name='In Absentia', music_band_id=1, user_id=1, description="In Absentia is the seventh studio album by British progressive rock band Porcupine Tree, first released on 24 September 2002. The album marked several changes for the band, with it being the first with new drummer Gavin Harrison and the first to move into a more heavy metal and progressive metal direction, contrary to past albums' psychedelic and pop rock sounds. Additionally, it was their first release on a major record label, Lava Records. It was very well received critically and commercially, with it often being considered the band's crowning achievement, and selling over triple what any of the band's prior albums had in the past."))
session.commit()

session.add(Album(name='In Absentia', music_band_id=1, user_id=1, description="In Absentia is the seventh studio album by British progressive rock band Porcupine Tree, first released on 24 September 2002. The album marked several changes for the band, with it being the first with new drummer Gavin Harrison and the first to move into a more heavy metal and progressive metal direction, contrary to past albums' psychedelic and pop rock sounds. Additionally, it was their first release on a major record label, Lava Records. It was very well received critically and commercially, with it often being considered the band's crowning achievement, and selling over triple what any of the band's prior albums had in the past."))
session.commit()

session.add(Album(name='Meteora', music_band_id=1, user_id=1, description="Meteora is the second studio album by American rock band Linkin Park. It was released on March 25, 2003 through Warner Bros. Records, following Reanimation, a collaboration album which featured remixes of songs included on their debut studio album Hybrid Theory. The album was produced by the band alongside Don Gilmore. The title Meteora is taken from the Greek Orthodox monasteries sharing the same name."))
session.commit()

session.add(Album(name='Deadwing', music_band_id=2, user_id=1, description="Deadwing is the eighth studio album by British progressive rock band Porcupine Tree, released on 28 March 2005. It quickly became the band's best selling album, although it was later surpassed by Fear of a Blank Planet. The album is based on a screenplay written by Steven Wilson and Mike Bennion, and is essentially a ghost story. Wilson had expressed the intention to eventually have this film script made into a movie."))
session.commit()

session.add(Album(name='Phobia', music_band_id=3, user_id=1, description="Phobia is the third studio album by American rock band Breaking Benjamin. It was recorded at The Barbershop Studios in Hopatcong, New Jersey and released August 8, 2006 through Hollywood Records and November 21, 2007 in Europe."))
session.commit()

session.add(Album(name='New Bermuda', music_band_id=5, user_id=1, description="New Bermuda is the third studio album by American blackgaze band Deafheaven. It was released on October 2, 2015 through ANTI- record label."))
session.commit()

session.add(Album(name='To the Bone', music_band_id=6, user_id=1, description="To the Bone is the fifth studio album by English recording artist Steven Wilson, released on 18 August 2017 on Caroline International. It was recorded two-and-a-half years after the release of Hand. Cannot. Erase. (2015), and one year after his mini-album, (2016).[1] According to Wilson, the album is inspired by the progressive pop records of his youth, such as Peter Gabriel's So, Kate Bush's Hounds of Love, Talk Talk's The Colour of Spring, and Tears for Fears' The Seeds of Love."))
session.commit()

session.add(Album(name="That's the Spirit", music_band_id=7, user_id=1, description="That's the Spirit is the fifth studio album by British rock band Bring Me the Horizon. The album was released on 11 September 2015,[1] and marks a departure from the group's metalcore roots, in favour of a less aggressive rock style."))
session.commit()

session.add(Album(name='The sorrow of september', music_band_id=8,user_id=1,description="As as french project, this was the first landmark album from the band"))
session.commit()






