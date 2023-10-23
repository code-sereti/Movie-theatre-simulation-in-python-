import collections
import random

import simpy


RANDOM_SEED = 42
TICKETS = 50
SIM_TIME = 120


def moviegoer(env, movie, num_tickets, theater):
   
    with theater.counter.request() as my_turn:
        result = yield my_turn | theater.sold_out[movie]

        if my_turn not in result:
            theater.num_renegers[movie] += 1
            return

        if theater.available[movie] < num_tickets:
            yield env.timeout(0.5)
            return


        theater.available[movie] -= num_tickets
        if theater.available[movie] < 2:
            theater.sold_out[movie].succeed()
            theater.when_sold_out[movie] = env.now
            theater.available[movie] = 0
        yield env.timeout(1)


def customer_arrivals(env, theater):
    while True:
        yield env.timeout(random.expovariate(1 / 0.5))

        movie = random.choice(theater.movies)
        num_tickets = random.randint(1, 6)
        if theater.available[movie]:
            env.process(moviegoer(env, movie, num_tickets, theater))


Theater = collections.namedtuple('Theater', 'counter, movies, available, '
                                            'sold_out, when_sold_out, '
                                            'num_renegers')



print('Movie renege')
random.seed(RANDOM_SEED)
env = simpy.Environment()

counter = simpy.Resource(env, capacity=1)
movies = ['Python Unchained', 'Kill Process', 'Pulp Implementation']
available = {movie: TICKETS for movie in movies}
sold_out = {movie: env.event() for movie in movies}
when_sold_out = {movie: None for movie in movies}
num_renegers = {movie: 0 for movie in movies}
theater = Theater(counter, movies, available, sold_out, when_sold_out,
                  num_renegers)


env.process(customer_arrivals(env, theater))
env.run(until=SIM_TIME)


for movie in movies:
    if theater.sold_out[movie]:
        print('Movie "%s" sold out %.1f minutes after ticket counter '
              'opening.' % (movie, theater.when_sold_out[movie]))
        print('  Number of people leaving queue when film sold out: %s' %
              theater.num_renegers[movie])
