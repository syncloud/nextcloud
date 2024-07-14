FROM php:8.3.9-fpm-bullseye
RUN apt-get update && apt-get install -y \
		libfreetype6-dev \
		libjpeg62-turbo-dev \
		libpng-dev \
		libzip-dev \
		libsmbclient-dev \
		libxml2-dev \
		libsqlite3-dev \
		libpq-dev \
		libldap2-dev \
		libsasl2-dev \
		libfreetype6-dev \
		liblqr-1-0-dev \
		libfftw3-dev \
		libjbig-dev \
		libtiff5-dev \
		libwebp-dev \
		libmemcached-dev \
 libmcrypt-dev \
		zip \
		wget \
		unzip \
 libgmp-dev \
 libonig-dev \
 libicu-dev \
 libmagickwand-dev \
 libbz2-dev \
 git \
  --no-install-recommends

RUN mkdir -p /usr/src/php/ext/memcached
WORKDIR /usr/src/php/ext/memcached
RUN wget https://github.com/php-memcached-dev/php-memcached/archive/v3.1.5.zip; unzip /usr/src/php/ext/memcached/v*.zip
RUN mv /usr/src/php/ext/memcached/php-memcached-*/* /usr/src/php/ext/memcached/

RUN docker-php-ext-install bz2
RUN docker-php-ext-configure memcached
RUN docker-php-ext-install memcached
RUN docker-php-ext-install gmp
#RUN pecl install imagick
RUN git clone https://github.com/Imagick/imagick.git --depth 1 /tmp/imagick && \
    cd /tmp/imagick && \
    git fetch origin master && \
    git switch master && \
    cd /tmp/imagick && \
    phpize && \
    ./configure && \
    make && \
    make install && \
    docker-php-ext-enable imagick

RUN pecl install smbclient
RUN pecl install apcu
RUN pecl install mcrypt-1.0.7
RUN pecl install redis
RUN docker-php-ext-enable redis
RUN docker-php-ext-configure intl
RUN docker-php-ext-install intl
RUN docker-php-ext-enable apcu
RUN docker-php-ext-install ldap
RUN docker-php-ext-enable mcrypt
RUN docker-php-ext-install bcmath
RUN docker-php-ext-install pdo_mysql
RUN docker-php-ext-install mysqli
RUN docker-php-ext-install mbstring
RUN docker-php-ext-install opcache
RUN docker-php-ext-install zip
RUN docker-php-ext-install pcntl
RUN docker-php-ext-install exif
RUN docker-php-ext-install sysvsem
#RUN docker-php-ext-enable imagick

RUN docker-php-ext-enable smbclient
RUN docker-php-ext-install pdo pdo_pgsql
RUN docker-php-ext-configure gd --with-freetype --with-jpeg
RUN docker-php-ext-install -j2 gd
RUN rm -rf /var/lib/apt/lists/*
RUN apt remove -y git



