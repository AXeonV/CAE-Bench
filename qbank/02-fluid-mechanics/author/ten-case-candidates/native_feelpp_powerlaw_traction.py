"""Finite reviewed steady2D traction case using the shared native adapter."""
import native_feelpp_powerlaw_first as producer

if __name__=='__main__':
    producer.CASE='ch02-2-1-5-06-power_law_traction'
    producer.main()
