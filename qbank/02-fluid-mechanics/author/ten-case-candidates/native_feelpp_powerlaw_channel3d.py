"""Finite reviewed3D channel using stock Feel++ and the shared I/O adapter."""
import native_feelpp_powerlaw_first as producer

if __name__=='__main__':
    producer.CASE='ch02-2-1-7-01-power_law_channel'
    producer.main()
