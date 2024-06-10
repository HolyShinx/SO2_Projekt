## Maszyna do piłeczek tenisowych (nazwa tymczasowa, nie mam lepszej na razie, formalne "GameBall")

Obraz koncepcyjny:
![b0c4f3f4-694d-476d-ae7b-3b72280923c5](https://github.com/HolyShinx/SO2_Projekt/assets/71772288/ffa19852-9d63-42b0-a30c-2a80681a1d42)

"Gameball" jest prostą grą stworzoną w języku python, dzieki bibliotece pygame.
Jest to aplikacja wielowątkowa, obsługuje wielowątkowość za pomocą modułu "threading".
Gra ta jest dość prosta, leci piłka w stronę gracza, a gracz ma ją odbić. Żeby było tą grę czuć, dodałem wiele efektów typu kręcenie piłki, odlot piłki czy dźwięk gdy piłka jest
w połowie drogi, efekt ten po części osiągnąłem, a tryb podwójny jest jeszcze przyjemniejszy.
Objekty rysowałem ja, tła mi bot wygenerował, ten projekt zajął mi dłużej niż powinien xd

Objekty przybliżone i krótko opisane co się dzieje na ekranie 
![image](https://github.com/HolyShinx/SO2_Projekt/assets/71772288/7bc1ae58-85f3-482f-b935-daffef573cca)


### Wątki
**Projectile** - Wątek odpowiedzialny za pocisk lecący w strone gracza z punktu wyrzutni, gracz musi go odbić aby zyskać punkt i nie przegrać

**Projectile_Top** - Kopia wątku pierwszego bez obsługi metronomu

**Baseball** - Wątek odpowiedziany za akcję gracza (machanie kijem) i jej konsekwencje

**FlyingProjectile** - Wątek służący do zarządzania pozycją i stanem dekoracyjnego pocisku po trafieniu "Projectile", nie ma praktycznego zastosowania, poza daniem graczu świadomości że trafił w piłkę

**ScoreManager** - Wątek do zarządzania wartością punktów, dodaje za trafienia, odejmuje za pudła

### Sekcje krytyczne:
**Projectile** - 2 Muteksy:

**Ruch pocisku i stan** - każdy wątek pocisku modyfikuje pozycje pocisku i sprawdza/aktualizuje jego status - celem tego zabiegu jest powstrzymanie przypadku wyścigu, aby pocisk nie był odczytany w stanie niepewnym

**Przejście przez centrum ekrany** - sekcja aktualizuje flage i puszcza dźwięk metronomu, synchronizacja w celu zapewnienia że tylko raz dźwięk zabrzmi

**Baseball** - 2 Muteksy

**Detekcja kolizji** - Sprawdza kolizje pomiędzy pociskiem, zmienne używane do sprawdzenia kolizji są używane przez inne wątki (pozycja)

Flagi Porażki i Czekania - Muteks ten upewnia się że flagi są synchonizowane z innymi wątkami

FlyingProjectile - muteks w celu uniknięcia drobnych wizualnych anomalii spowodowany niepoprawnym odczytem pozycji startowej

ScoreManager - dostęp do punktacji jest zlockowany w celu uniknięcia wielokrotnej modyfikacji
